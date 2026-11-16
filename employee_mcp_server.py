from mcp.server.fastmcp import FastMCP, Context
from typing import Literal, Optional
from pydantic import BaseModel, Field
import logging

# 1. Base Configuration setup
logging.basicConfig(
    level=logging.INFO,                           # Set minimum severity level to log
    format='%(asctime)s - %(levelname)s - %(message)s', # Define log layout structure
    datefmt='%Y-%m-%d %H:%M:%S'                    # Style the timestamp output
)

# 2. Instantiate a module-level logger 
logger = logging.getLogger(__name__)

mcp = FastMCP("employee_mcp_server")

class Employee(BaseModel):
    name: str
    personal_email: str
    official_email: str
    address: str
    department: Literal["Engineering", "HR", "IT Support", "Infra"]

class MissingFieldInput(BaseModel):
    accept: bool = Field(description="Accept the result!")
    name: Optional[str]
    personal_email: Optional[str]
    official_email: Optional[str]
    address: Optional[str]
    department: Optional[str]

@mcp.tool(name="onboard_new_employee", description="Insert the employee into database as a record")
async def onboard_new_employee(personal_email: str, ctx: Context):
    try:
        if not personal_email or len(personal_email.strip()) == 0:
            return {
                "status": 1001, 
                "message": "Kindly fill the missing fields data", 
                "response": {"missing_fields": "personal_email"}
            }
        
        # if len(missing_fields) > 0:
        #     return {"status": 1001, "message": "Kindly fill the missing fields data", "response": {"missing_fields": missing_fields}}
        # logger.info(f"""
        # Employee Name: {name}
        # Personal Email: {personal_email}
        # Official Email: {official_email}
        # Address: {address}
        # Department: {department}
        # """)
        return {"status": 201, "message": "Employee has been onboarded successfully"}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": 500, "message": f"Error: {e}"}
    
@mcp.tool(name="deboard_employee", description="Delete the particular employee from database")
def deboard_employee(email: str):
    try:
        if not email:
            raise Exception("DEBOARD_EMPLOYEE: official email is required field")
        print(f"Personal Email: {email}")
        return {"status": 201, "message": "Employee has been deboarded successfully"}
    except Exception as e:
        print(f"Error: {e}")
        return {"status": 500, "message": f"Error: {e}"}

@mcp.tool(name="get_employees", description="Get the particular employee")
def get_employees():
    try:
        return {"status": 201, "message": "Employee has been fetched successfully", "response": [Employee(name="Abc", personal_email="Abc@myorgemail.com", official_email="OfficeAbc@myorgemail.com", address="Abc Home", department="Engineering")]}
    except Exception as e:
        print(f"Error: {e}")
        return {"status": 500, "message": f"Error: {e}"}

@mcp.tool(name="get_employee", description="Get the particular employee by name")
def get_employee(name: str):
    try:
        return {"status": 201, "message": "Employee has been fetched successfully", "response": [Employee(name="Abc", personal_email="Abc@myorgemail.com", official_email="OfficeAbc@myorgemail.com", address="Abc Home", department="Engineering")]}
    except Exception as e:
        print(f"Error: {e}")
        return {"status": 500, "message": f"Error: {e}"}

@mcp.tool(name="update_employee", description="Update the particular employee")
def update_employee(name: str, personal_email: str, official_email: str, address: str, department: Literal["Engineering", "HR", "IT Support"]):
    try:
        if not name or not personal_email:
            raise Exception("name and personal email are required fields")
        print(f"""
        Employee Name: {name}
        Personal Email: {personal_email}
        Official Email: {official_email}
        Address: {address}
        Department: {department}
        """)
        return {"status": 201, "message": "Employee has been updated successfully!"}
    except Exception as e:
        print(f"Error: {e}")
        return {"status": 500, "message": f"Error: {e}"}

@mcp.tool(name="validate_employee_details", description="Validate employee details")
def validate_employee_details(email: str):
    try:
        if not email:
            raise Exception("VALIDATE_EMPLOYEE_DETAILS: official email is required field")
        print(f"Personal Email: {email}")
        return {"status": 201, "message": "Employee has been validated successfully"}
    except Exception as e:
        print(f"Error: {e}")
        return {"status": 500, "message": f"Error: {e}"}

if __name__ == "__main__":
    mcp.run(transport="stdio")