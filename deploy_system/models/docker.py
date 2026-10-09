from dataclasses import dataclass 
from subprocess import CompletedProcess
from pathlib import Path
#外部執行果會儲存停止的階段，而停止以前的階段表示執行成功
@dataclass
class docker:
    name:str
    id : str
    label: (str|None)
    status:str
    port:int
    project_path:Path
