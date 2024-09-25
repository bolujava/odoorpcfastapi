from pydantic import BaseModel

import odoorpc
from fastapi import FastAPI, HTTPException

app = FastAPI()


odoo = odoorpc.ODOO('demo6.odoo.com', protocol='jsonrpc+ssl', port=443)

db = 'demo_saas-174_71d1464473f4_1727275673'
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
    try:
        Partner = odoo.env['res.partner']
        success = Partner.write([partner_id], {'name': update_data.name})
        if success:
            updated_partner = Partner.read([partner_id], ['name'])
            return {"message": "Partner updated successfully", "updated_partner": updated_partner}
        else:
            raise HTTPException(status_code=500, detail="Failed to update partner")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating partner: {e}")


@app.delete("/partners/{partner_id}")
def delete_partner(partner_id: int):
    if odoo is None:
        raise HTTPException(status_code=500, detail="Failed to connect")
    try:
        Partner = odoo.env['res.partner']
        success = Partner.unlink([partner_id])
        if success:
            return {"message": "Partner deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete partner")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting partner: {e}")



@app.get("/sales-order")
def get_sales_order():
    if odoo is None:
        raise HTTPException(status_code=500, detail="Failed to connect")
    try:
        SaleOrder = odoo.env['sale.order']


        sales_order_ids = SaleOrder.search([])  # Ensure this does not return an empty list
        if not sales_order_ids:
            return {"message": "No sales orders found"}


        sales_orders = SaleOrder.read(sales_order_ids, ['name', 'partner_id', 'amount_total', 'date_order', 'state'])


        sales_order_list = [{
            "id": order["id"],
            "name": order["name"],
            "customer": order["partner_id"][1] if order["partner_id"] else "N/A",  # Check for partner existence
            "amount_total": order["amount_total"],
            "date_order": order["date_order"],
            "state": order["state"]
        } for order in sales_orders]

        return sales_order_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sales orders: {e}")


@app.get("/available_models")
def list_models():
    if odoo is None:
        raise HTTPException(status_code=500, detail="Failed to connect to Odoo")
    try:
        models = odoo.env['ir.model'].search([])
        model_names = odoo.env['ir.model'].read(models, ['model'])
        return {"available_models": [model['model'] for model in model_names]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {e}")



# @app.post("/sales-order/{order_id}/invoice")
# def post_invoice(order_id: int):
#     if odoo is None:
#         raise HTTPException(status_code=500, detail="Failed to connect to Odoo")
#     try:
#         SaleOrder = odoo.env['sale.order']
#         Invoice = odoo.env['account.move']
#
#         order = SaleOrder.browse(order_id)
#         if not order.exists() or order.state not in ['sale', 'done']:
#             raise HTTPException(status_code=400, detail="Sales order is not confirmed or does not exist")
#         invoice_id = order.create_invoices()
#         if not invoice_id:
#             raise HTTPException(status_code=500, detail="Invoice could not be created")
#         invoice = Invoice.browse(invoice_id)
#         invoice.action_post()
#         return {"message": "Invoice posted successfully", "invoice_id": invoice.id}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error posting invoice {e}")


@app.post("/sales-order/{order_id}/invoice")
def post_invoice(order_id: int):
    if odoo is None:
        raise HTTPException(status_code=500, detail="Failed to connect to Odoo")
    try:
        SaleOrder = odoo.env['sale.order']
        AccountMove = odoo.env['account.move']

        order = SaleOrder.browse(order_id)
        if not order.exists() or order.state not in ['sale', 'done']:
            raise HTTPException(status_code=400, detail="Sales order is not confirmed or does not exist")

        # Create the invoice manually
        invoice_vals = {
            'move_type': 'out_invoice',  # Customer invoice
            'partner_id': order.partner_id.id,
            'invoice_origin': order.name,
            'invoice_line_ids': [(0, 0, {
                'name': order.order_line[0].name,
                'quantity': order.order_line[0].product_uom_qty,
                'price_unit': order.order_line[0].price_unit,
                'account_id': 1,  # Replace with a valid account_id
            })],
        }

        invoice_id = AccountMove.create(invoice_vals)
        invoice = AccountMove.browse(invoice_id.id)

        invoice.action_post()  # Post the invoice if required

        return {"message": "Invoice created and posted successfully", "invoice_id": invoice.id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error posting invoice: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)



