import os
import tempfile

tempdir = tempfile.gettempdir()

path = os.path.abspath(os.path.join(os.path.dirname(__file__), "compiler.jar"))
if not os.path.exists(path):
    raise Exception("No closure compiler.jar at %s; Download from http://closure-compiler.googlecode.com/files/compiler-latest.zip" % path)

# Useful extra_params:
#   --compilation_level WHITESPACE_ONLY
#   --strict_mode_input false
def minimize(code, extra_params=""):
    # Cannot keep these files open on Windows since file cannot then be read by Java
    ntf = tempfile.NamedTemporaryFile(delete=False)
    if not isinstance(code, bytes):
        code = code.encode("utf-8")
    ntf.write(code)
    ntf.flush()
    ntf.close()

    ntf2 = tempfile.NamedTemporaryFile(delete=False)
    ntf2.close()

    ret = os.system("java -jar %s %s --js %s --js_output_file %s" % (path, extra_params, ntf.name, ntf2.name))
    if ret:
        # Error!
        raise RuntimeError("Closure Compiler Error")
    ntf2 = open(ntf2.name, "r")
    data = ntf2.read()
    ntf2.close()
    os.unlink(ntf2.name)
    os.unlink(ntf.name)
    return data
