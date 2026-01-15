from flask import jsonify

class validator:
    @staticmethod
    def sale_data(data):
        #TODO: Better sale data validation

        saleId = data.get("id")
        item = data.get("item")
        quantity = data.get("quantity")
        amountPaid = data.get("revenue")
        date = data.get("sale_time")
        paymentMethod = data.get("payment_method")

        defaultError = {"success":False, "error":"Insert error messageA"}
        if not item:
            return False, {"success":False, "error":"Insert error messageB"}
        if not isinstance(quantity, int):
            return False, {"success":False, "error":"Insert error messageC"}
        if quantity <0:
            return False, {"success":False, "error":"Insert error messageD"}
        if not isinstance(amountPaid, (int, float)):
            return False, {"success":False, "error":"Insert error messageE"}
        if amountPaid < 0:
            return False, {"success":False, "error":"Insert error messageF"}
        if not date:
            return False, {"success":False, "error":"Insert error messageG"}
        if not paymentMethod:
            return False, {"success":False, "error":"Insert error messageH"}
        return True, None