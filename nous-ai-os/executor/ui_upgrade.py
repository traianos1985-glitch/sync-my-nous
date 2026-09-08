from executor.secure_patch import secure_patch

HTML_UPGRADE = r'''
<style>

.topbar{
    display:flex;
    gap:10px;
    margin-bottom:15px;
}

button{
    background:#0f0;
    color:#000;
    border:none;
    padding:10px;
    font-weight:bold;
    cursor:pointer;
}

#dashboard{
    display:none;
    border:1px solid #0f0;
    padding:10px;
    margin-top:20px;
}

.app-card{
    border:1px solid #0f0;
    padding:10px;
    margin-top:10px;
}

.input-row{
    display:flex;
    gap:10px;
}

#cmd{
    flex:1;
}

</style>

<div class="topbar">

<button onclick="toggleDashboard()">
DASHBOARD
</button>

<button onclick="showMemory()">
MEMORY
</button>

<button onclick="runEvolution()">
EVOLVE
</button>

</div>

<div id="dashboard">

<h3>ΝΟΥΣ APPLICATIONS</h3>

<div class="app-card">
PLUGIN SYSTEM
</div>

<div class="app-card">
SELF HEALING
</div>

<div class="app-card">
LOCAL LLM BRIDGE
</div>

<div class="app-card">
AUTONOMOUS ENGINE
</div>

</div>

<script>

function toggleDashboard(){

    const d = document.getElementById("dashboard");

    if(d.style.display === "block"){
        d.style.display = "none";
    } else {
        d.style.display = "block";
    }
}

async function showMemory(){

    cmd.value = "/memory";
    cmd.dispatchEvent(
        new KeyboardEvent(
            "keydown",
            {key:"Enter"}
        )
    );
}

async function runEvolution(){

    cmd.value = "/auto-evolve";
    cmd.dispatchEvent(
        new KeyboardEvent(
            "keydown",
            {key:"Enter"}
        )
    );
}

</script>
'''

def apply_ui_upgrade():

    with open("executor/router.py", "r") as f:
        text = f.read()

    if "DASHBOARD" in text:

        return {
            "status": "already upgraded"
        }

    text = text.replace(
        '<div id="output"></div>',
        '<div id="output"></div>' + HTML_UPGRADE
    )

    text = text.replace(
        '<input\n    id="cmd"',
        '''
<div class="input-row">

<input
    id="cmd"
'''
    )

    text = text.replace(
        '/>\n\n<script>',
        '''/>

<button onclick="
cmd.dispatchEvent(
new KeyboardEvent(
'keydown',
{key:'Enter'}
)
)
">
SEND
</button>

</div>

<script>
'''
    )

    secure_patch(
        "executor/router.py",
        text
    )

    return {
        "status": "ui upgraded"
    }

if __name__ == "__main__":

    print(
        apply_ui_upgrade()
    )
