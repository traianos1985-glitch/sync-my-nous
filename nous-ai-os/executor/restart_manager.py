import os

def restart():
    print("RESTARTING SERVER...")
    os.system("pkill -f clean_agent.py")
    os.system("nohup python clean_agent.py > logs/server.log 2>&1 &")

if __name__ == "__main__":
    restart()
