from http.client import HTTPException
from logging import exception, raiseExceptions
from pydantic import BaseModel

import odoorpc
from fastapi import FastAPI

app = FastAPI()


odoo = odoorpc.ODOO('demo6.odoo.com', protocol='jsonrpc+ssl', port=443)

db = 'demo_saas-174_015c4c323f2d_1727073759'
username = 'admin'
password = 'admin'

class PartnerUpdateRequest(BaseModel):
    name: str



try:
    odoo.login(db, username, password)
except Exception as e:
    print(f"Error logging in: {e}")
    odoo = None


@app.get("/user_details", summary="This gives the login details of the users", response_model=dict)
def login_user_details():
    if odoo is None :
        raise HTTPException(status_code = 500, detail = "failed to connect")
    user = odoo.env.user
    return {"username":user.name,"ID":user.id}

@app.get("/")
def root():
    return {"we are here"}

@app.get("/partners")
def get_partners():
    Partner = odoo.env['res.partner']
    partners = Partner.search([])
    partner_list = [{"id":partner.id, "name":partner.name}for partner in Partner.browse(partners)]
    return partner_list

@app.get("/check_access")
def checking_access_right():
    try:
        has_access = odoo.env['res.partner'].check_access_right('read', raise_exception = False)
    except Exception as e:
        raise HTTPException(status_code= 500, detail = f"Error checking access right: {e}")
    return has_access


@app.put("/partners/{partner_id}")
def update_partner(partner_id: int, update_data: PartnerUpdateRequest):
    if odoo is None:
        raise HTTPException(status_code=500, detail="Failed to connect to Odoo")
    Partner = odoo.env['res.partner']
    try:

        success = Partner.write([partner_id], {'name': update_data.name})
        if success:
            updated_partner = Partner.read([partner_id], ['name'])
            return {"message": "Partner updated successfully", "updated_partner": updated_partner}
        else:
            raise HTTPException(status_code=500, detail="Failed to update records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating partner: {e}")


@app.delete("/partners/{partner_id}")
def delete_partner(partner_id: int):
    if odoo is None:
        raise HTTPException(status_code=500, detail="Failed to connect")
    Partner = odoo.env['res.partner']

    try:
        success = Partner.unlink([partner_id])
        if success:
            return {"message": "Partner deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete partner")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting partner: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)



