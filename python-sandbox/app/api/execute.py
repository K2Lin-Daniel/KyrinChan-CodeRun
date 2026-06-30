import os
import sys
import subprocess
import tempfile
import base64
import shutil
from fastapi import APIRouter
from models.schemas import CodeRequest, CodeResponse

router = APIRouter()

@router.post("/execute", response_model=CodeResponse)
def execute_code(request: CodeRequest):
    code = request.code

    # Create a unique temporary directory (fallback to system temp dir if /tmp doesn't exist or is not writable)
    temp_parent = "/tmp" if os.path.exists("/tmp") and os.access("/tmp", os.W_OK) else None
    run_dir = tempfile.mkdtemp(dir=temp_parent, prefix="run-")
    
    # Paths for all files inside the run directory
    code_file_path = os.path.join(run_dir, "user_code.py")
    runner_file_path = os.path.join(run_dir, "runner.py")
    stdout_file_path = os.path.join(run_dir, "stdout.log")
    stderr_file_path = os.path.join(run_dir, "stderr.log")

    try:
        # Write request files if present
        if request.files:
            for filename, b64_content in request.files.items():
                clean_filename = os.path.basename(filename)
                if not clean_filename or clean_filename in (".", ".."):
                    continue
                file_path = os.path.join(run_dir, clean_filename)
                try:
                    if "," in b64_content:
                        b64_content = b64_content.split(",", 1)[1]
                    file_data = base64.b64decode(b64_content)
                    with open(file_path, "wb") as f:
                        f.write(file_data)
                except Exception:
                    # Ignore write failures for specific files
                    pass

        # Write user code to file
        with open(code_file_path, "w", encoding="utf-8") as f:
            f.write(code)

        # Inline runner script to enforce resource limits before executing the user code
        runner_script = f"""
import sys
import runpy

# Enforce resource limits
try:
    import resource
    MAX_VIRTUAL_MEMORY = {request.memory_limit_mb} * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (MAX_VIRTUAL_MEMORY, MAX_VIRTUAL_MEMORY))

    MAX_CPU_TIME = {request.timeout}
    resource.setrlimit(resource.RLIMIT_CPU, (MAX_CPU_TIME, MAX_CPU_TIME))

    # Prevent fork bombs
    # resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))
except Exception as e:
    print(f"Warning: Failed to set resource limits: {{e}}", file=sys.stderr)

# Override user-specified fonts in matplotlib to ensure manually merged font is used
try:
    import matplotlib
    import matplotlib.font_manager
    import inspect

    # 1. Configure defaults
    matplotlib.rcParams['font.family'] = 'sans-serif'
    matplotlib.rcParams['font.sans-serif'] = ['SandboxFont', 'DejaVu Sans', 'Arial', 'Helvetica', 'sans-serif']
    matplotlib.rcParams['axes.unicode_minus'] = False

    if hasattr(matplotlib, 'rcParamsDefault'):
        matplotlib.rcParamsDefault['font.family'] = 'sans-serif'
        matplotlib.rcParamsDefault['font.sans-serif'] = ['SandboxFont', 'DejaVu Sans', 'Arial', 'Helvetica', 'sans-serif']
        matplotlib.rcParamsDefault['axes.unicode_minus'] = False

    # Keep original methods
    orig_setitem = matplotlib.RcParams.__setitem__
    orig_update = matplotlib.RcParams.update
    orig_setdefault = matplotlib.RcParams.setdefault
    orig_pop = matplotlib.RcParams.pop

    # 2. Patch RcParams to block any attempts to change font keys
    def patched_setitem(self, key, val):
        if key.startswith('font.') or key == 'font':
            return
        orig_setitem(self, key, val)
    matplotlib.RcParams.__setitem__ = patched_setitem

    def patched_update(self, *args, **kwargs):
        new_args = []
        if args:
            arg = args[0]
            if hasattr(arg, 'keys'):
                filtered_arg = {{k: v for k, v in arg.items() if not (k.startswith('font.') or k == 'font')}}
            else:
                filtered_arg = [(k, v) for k, v in arg if not (k.startswith('font.') or k == 'font')]
            new_args.append(filtered_arg)
        new_kwargs = {{k: v for k, v in kwargs.items() if not (k.startswith('font.') or k == 'font')}}
        orig_update(self, *new_args, **new_kwargs)
    matplotlib.RcParams.update = patched_update

    def patched_setdefault(self, key, default=None):
        if key.startswith('font.') or key == 'font':
            return self.get(key)
        return orig_setdefault(self, key, default)
    matplotlib.RcParams.setdefault = patched_setdefault

    def patched_pop(self, key, *args):
        if key.startswith('font.') or key == 'font':
            return self.get(key)
        return orig_pop(self, key, *args)
    matplotlib.RcParams.pop = patched_pop

    def restore_our_fonts():
        orig_setitem(matplotlib.rcParams, 'font.family', 'sans-serif')
        orig_setitem(matplotlib.rcParams, 'font.sans-serif', ['SandboxFont', 'DejaVu Sans', 'Arial', 'Helvetica', 'sans-serif'])
        orig_setitem(matplotlib.rcParams, 'axes.unicode_minus', False)
        if hasattr(matplotlib, 'rcParamsDefault'):
            orig_setitem(matplotlib.rcParamsDefault, 'font.family', 'sans-serif')
            orig_setitem(matplotlib.rcParamsDefault, 'font.sans-serif', ['SandboxFont', 'DejaVu Sans', 'Arial', 'Helvetica', 'sans-serif'])
            orig_setitem(matplotlib.rcParamsDefault, 'axes.unicode_minus', False)

    # 3. Patch rcdefaults to restore our fonts
    orig_rcdefaults = matplotlib.rcdefaults
    def patched_rcdefaults():
        orig_rcdefaults()
        restore_our_fonts()
    matplotlib.rcdefaults = patched_rcdefaults

    # 4. Patch FontProperties to override family/fname during instantiation
    FontProperties = matplotlib.font_manager.FontProperties
    orig_fp_init = FontProperties.__init__
    orig_set_family = FontProperties.set_family if hasattr(FontProperties, 'set_family') else None
    orig_set_fname = FontProperties.set_fname if hasattr(FontProperties, 'set_fname') else None
    orig_set_file = FontProperties.set_file if hasattr(FontProperties, 'set_file') else None

    def patched_fp_init(self, *args, **kwargs):
        orig_fp_init(self, *args, **kwargs)
        if orig_set_family:
            orig_set_family(self, 'sans-serif')
        if orig_set_fname:
            orig_set_fname(self, None)
        elif orig_set_file:
            orig_set_file(self, None)

    FontProperties.__init__ = patched_fp_init

    # 5. Patch FontProperties setters to force target values
    if hasattr(FontProperties, 'set_family'):
        FontProperties.set_family = lambda self, family: orig_set_family(self, 'sans-serif')

    if hasattr(FontProperties, 'set_fontname'):
        orig_set_fontname = FontProperties.set_fontname
        FontProperties.set_fontname = lambda self, family: orig_set_fontname(self, 'sans-serif')

    if hasattr(FontProperties, 'set_name'):
        orig_set_name = FontProperties.set_name
        FontProperties.set_name = lambda self, family: orig_set_name(self, 'sans-serif')

    if hasattr(FontProperties, 'set_fname'):
        FontProperties.set_fname = lambda self, fname: orig_set_fname(self, None)

    if hasattr(FontProperties, 'set_file'):
        FontProperties.set_file = lambda self, fname: orig_set_file(self, None)

except Exception as e:
    print("Warning: Failed to override matplotlib fonts:", e, file=sys.stderr)

# Execute user code
try:
    runpy.run_path({repr(code_file_path)}, run_name="__main__")
    
    # Auto-save active matplotlib figures if matplotlib is imported
    import sys
    if "matplotlib.pyplot" in sys.modules:
        try:
            import matplotlib.pyplot as plt
            fignums = plt.get_fignums()
            for idx, fignum in enumerate(fignums):
                fig = plt.figure(fignum)
                filename = "plot.png" if idx == 0 else f"plot_{{idx + 1}}.png"
                fig.savefig(filename, dpi=200, bbox_inches="tight")
        except Exception as e:
            print(f"Warning: Failed to auto-save matplotlib figure: {{e}}", file=sys.stderr)
except SystemExit as e:
    sys.exit(e.code)
except Exception:
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""

        with open(runner_file_path, "w", encoding="utf-8") as f:
            f.write(runner_script)

        stdout_file = open(stdout_file_path, "w+", encoding="utf-8")
        stderr_file = open(stderr_file_path, "w+", encoding="utf-8")

        # Setup environment variables for the subprocess
        env = os.environ.copy()
        env["MPLBACKEND"] = "Agg"
        # Use shared writable matplotlib config directory if available, fallback to task-specific dir
        shared_cache = "/tmp/.matplotlib"
        if os.path.isdir(shared_cache):
            env["MPLCONFIGDIR"] = shared_cache
        else:
            env["MPLCONFIGDIR"] = os.path.join(run_dir, ".matplotlib")

        process = subprocess.Popen(
            [sys.executable, runner_file_path],
            stdout=stdout_file,
            stderr=stderr_file,
            cwd=run_dir,
            env=env,
            text=True
        )

        try:
            # Wall-clock timeout is slightly longer than CPU time limit
            process.wait(timeout=request.timeout + 1)
            exit_code = process.returncode
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            exit_code = 137 # Standard exit code for SIGKILL
            stderr_file.write("\nExecution timed out (Wall-clock limit reached).")
            stderr_file.flush()

        # Close files to read content
        stdout_file.close()
        stderr_file.close()

        MAX_OUTPUT_LENGTH = 100000

        def read_limited_output(file_path):
            if not os.path.exists(file_path):
                return ""
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(MAX_OUTPUT_LENGTH + 1)
                if len(content) > MAX_OUTPUT_LENGTH:
                    return content[:MAX_OUTPUT_LENGTH] + "\n...[Output truncated due to length limit]..."
                return content

        stdout = read_limited_output(stdout_file_path)
        stderr = read_limited_output(stderr_file_path)

        # Collect generated image files
        images = {}
        img_extensions = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml"
        }

        if os.path.exists(run_dir):
            for filename in sorted(os.listdir(run_dir)):
                file_path = os.path.join(run_dir, filename)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in img_extensions:
                        try:
                            with open(file_path, "rb") as img_file:
                                img_data = img_file.read()
                                if img_data:
                                    base64_data = base64.b64encode(img_data).decode("utf-8")
                                    mime_type = img_extensions[ext]
                                    images[filename] = f"data:{mime_type};base64,{base64_data}"
                        except Exception:
                            pass

        return CodeResponse(stdout=stdout, stderr=stderr, exit_code=exit_code, images=images)

    except Exception as e:
        return CodeResponse(stdout="", stderr=str(e), exit_code=-1, images={})
        
    finally:
        if 'stdout_file' in locals() and not stdout_file.closed:
            stdout_file.close()
        if 'stderr_file' in locals() and not stderr_file.closed:
            stderr_file.close()
        if os.path.exists(run_dir):
            shutil.rmtree(run_dir, ignore_errors=True)

