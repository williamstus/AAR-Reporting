# File: src/debug_main.py
import sys
import traceback

print(">>> debug_main starting")

try:
    # Import your existing app module
    from src.main import EnhancedSoldierReportApplication
except Exception as e:
    print("!!! Failed to import EnhancedSoldierReportApplication from src.main")
    traceback.print_exc()
    sys.exit(2)

print(">>> creating application")
app = EnhancedSoldierReportApplication()

try:
    print(">>> calling initialize()")
    ok = app.initialize()
    print(f">>> initialize() returned: {ok}")
except Exception as e:
    print("!!! initialize() raised an exception")
    traceback.print_exc()
    sys.exit(3)

if not ok:
    print("!!! initialize() returned False (see logs). Exiting.")
    sys.exit(1)

try:
    print(">>> starting Tk mainloop")
    # Run the GUI loop directly to ensure it blocks
    app.main_window.root.update()
    app.main_window.root.deiconify()
    app.main_window.run()
    print(">>> mainloop exited cleanly")
except KeyboardInterrupt:
    print(">>> KeyboardInterrupt received")
except Exception:
    print("!!! Exception during mainloop")
    traceback.print_exc()
finally:
    print(">>> shutting down application")
    try:
        app.shutdown()
    except Exception:
        traceback.print_exc()

print(">>> debug_main finished")
