

import os
import sys
import streamlit.web.cli as stcli

sys.path.append("BiliMate")

if __name__ == "__main__":
    sys.argv = ["streamlit", "run", "./BiliMate/webui.py", "--server.port=8181"]
    stcli.main()


