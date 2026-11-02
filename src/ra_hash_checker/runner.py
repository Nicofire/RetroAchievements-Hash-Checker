from .api import ApiError, RetroAchievementsAPI
from .cache import CatalogStore
from .config import Settings
from .models import CheckResult, RunReport, Status, utc_now
from .native import HashError
from .registry import select_consoles
from .scanner import scan


def run(settings: Settings, store: CatalogStore | None = None) -> RunReport:
    consoles = select_consoles(settings.consoles)
    report = RunReport(settings.public_options())
    store = store or CatalogStore(
        settings.cache_dir, RetroAchievementsAPI(settings.api_key),
        offline=settings.offline, refresh=settings.refresh_cache,
        legacy_cache=settings.project_dir / ".ra_nds_games_cache.json",
    )
    try:
        if settings.default_roms:
            settings.paths[0].mkdir(parents=True, exist_ok=True)
        for candidate in scan(settings.paths, consoles, arcade_explicit="all" not in settings.consoles):
            result = CheckResult(
                path=str(candidate.path),
                console=candidate.console.slug if candidate.console else None,
                status=candidate.status or Status.UNCHECKED,
                message=candidate.message,
                candidates=list(candidate.candidates),
            )
            report.results.append(result)
            if candidate.status is not None or candidate.console is None:
                continue
            try:
                result.hash = candidate.console.calculate_hash(candidate.path)
            except (HashError, OSError, ValueError):
                result.status = Status.HASH_ERROR
                result.message = "Hash calculation failed: invalid file, format or disc structure."
                continue
            try:
                catalog = store.get(candidate.console.api_id)
            except ApiError as error:
                result.message = str(error)
                continue
            result.catalog_source = catalog.source
            result.catalog_fetched_at = catalog.fetched_at
            for warning in catalog.warnings:
                if warning not in report.warnings:
                    report.warnings.append(warning)
            result.games = catalog.index.get(result.hash, [])
            if not result.games:
                result.status = Status.UNKNOWN_HASH
            elif result.games[0].achievements:
                result.status = Status.SUPPORTED
            else:
                result.status = Status.NO_ACHIEVEMENTS
    except KeyboardInterrupt:
        report.completed = False
        if report.results and report.results[-1].status == Status.UNCHECKED:
            report.results[-1].message = "Check interrupted by the user."
    except OSError:
        report.warnings.append("The default ROM directory could not be created.")
    finally:
        report.ended_at = utc_now()
    return report