from mcp.server.fastmcp import FastMCP
import logging

# 1. Base Configuration setup
logging.basicConfig(
    level=logging.INFO,                           # Set minimum severity level to log
    format='%(asctime)s - %(levelname)s - %(message)s', # Define log layout structure
    datefmt='%Y-%m-%d %H:%M:%S'                    # Style the timestamp output
)

# 2. Instantiate a module-level logger 
logger = logging.getLogger(__name__)
mcp = FastMCP("department_mcp_server")

@mcp.tool(name="onboard_department", description="Onboard a new department")
def onboard_department(dept_name: str):
    if dept_name and dept_name.startswith('S'):
        return {"message": f"{dept_name} department is already exists", "status": 400}
    return {
         "message": "Department has been onboarded successfully",
         "status": 201
        }

@mcp.tool(name="dismiss_department", description="Dismiss the particular department")
def dismiss_department(dept_name: str):
    if dept_name and dept_name.startswith('S'):
        return {"message": f"{dept_name} department is not exists", "status": 400}
    return {
        "message": "Department has been deboarded successfully", 
        "status": 200
       }

@mcp.tool(name="update_department", description="Update the particular departments")
def update_department(source_name: str, destination_name: str):
    print(f"{source_name} source --> change to {destination_name} destination")
    return {
        "message": "Department has been update successfully", 
        "status": 200,
       }

@mcp.tool(name="get_departments", description="Fetch all the departments")
def get_departments():
    dept_names = ["DevOps", "Engineering", "HR", "Support"]
    dept_array = []
    for dept_name in dept_names:
        dept_array.append({
            "name": dept_name
        })
    return {
        "message": "Fetched all departments", 
        "status": 200,
        "response": dept_array
       }

if __name__ == "__main__":
    mcp.run(transport="stdio")