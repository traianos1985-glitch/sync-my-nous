import py_compile

def validate_python(path):
    try:
        py_compile.compile(path, doraise=True)
        return True
    except Exception as e:
        print("VALIDATION ERROR:", e)
        return False

if __name__ == "__main__":
    print("VALIDATOR READY")
