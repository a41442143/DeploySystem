from dataclasses import dataclass 
from subprocess import CompletedProcess

#外部執行果會儲存停止的階段，而停止以前的階段表示執行成功
@dataclass
class externalResult:
    stage:str
    success:bool
    message:str
    status_code : (int | None) = None

        
@dataclass

#如果result為None表示執行發生錯誤，但不確定具體錯誤，要自己看錯誤訊息
class ProcessResult:
    result : int | None
    stdout : str | None
    stderr: str
    time : float
    error_code : (int | None) = None
