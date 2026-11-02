#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <string.h>
#include "rc_hash.h"

static void capture_error(const char* message, const rc_hash_iterator_t* iterator)
{
    char* error = (char*)iterator->userdata;
    if (!error[0]) {
        strncpy(error, message, 1023);
        error[1023] = '\0';
    }
}

static PyObject* generate(PyObject* self, PyObject* args)
{
    const char* path;
    unsigned int console_id;
    char hash[33] = {0};
    char error[1024] = {0};
    int success;
    rc_hash_iterator_t iterator;
    (void)self;
    if (!PyArg_ParseTuple(args, "sI", &path, &console_id))
        return NULL;
    rc_hash_initialize_iterator(&iterator, path, NULL, 0);
    iterator.userdata = error;
    iterator.callbacks.error_message = capture_error;
    success = rc_hash_generate(hash, console_id, &iterator);
    rc_hash_destroy_iterator(&iterator);
    if (!success) {
        PyErr_SetString(PyExc_ValueError, error[0] ? error : "Hash calculation failed.");
        return NULL;
    }
    return PyUnicode_FromString(hash);
}

static PyMethodDef methods[] = {
    {"generate", generate, METH_VARARGS, "Generate the official RA hash for a path and console ID."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT, "_rcheevos", NULL, -1, methods,
    NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC PyInit__rcheevos(void)
{
    return PyModule_Create(&module);
}