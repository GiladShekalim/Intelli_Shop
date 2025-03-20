import jsonschema

# Define the coupon schema
coupon_schema = {
    "type": "object",
    "properties": {
        "id": {
            "type": "integer",
            "description": "Unique identifier for the coupon."
        },
        "code": {
            "type": "string",
            "description": "The code that customers will use to apply the coupon.",
            "pattern": "^[a-zA-Z0-9_]+$"  # Example pattern for alphanumeric with possible special characters
        },
        "amount": {
            "type": "number",
            "minimum": 0,
            "description": "The amount of discount provided by the coupon."
        },
        "date_created": {
            "type": "string",
            "format": "date-time",
            "description": "The date and time when the coupon was created."
        },
        "date_created_gmt": {
            "type": "string",
            "format": "date-time",
            "description": "The date and time when the coupon was created in GMT."
        },
        "date_modified": {
            "type": "string",
            "format": "date-time",
            "description": "The date and time when the coupon was last modified."
        },
        "date_modified_gmt": {
            "type": "string",
            "format": "date-time",
            "description": "The date and time when the coupon was last modified in GMT."
        },
        "discount_type": {
            "type": "string",
            "enum": ["percent", "fixed_cart", "fixed_product"],
            "description": "The type of discount provided by the coupon."
        },
        "description": {
            "type": ["string", "null"],
            "description": "A brief description of the coupon."
        },
        "date_expires": {
            "type": "string",
            "format": "date-time",
            "description": "The date and time when the coupon expires."
        },
        "date_expires_gmt": {
            "type": "string",
            "format": "date-time",
            "description": "The date and time when the coupon expires in GMT."
        },
        "usage_count": {
            "type": "integer",
            "minimum": 0,
            "description": "The number of times the coupon has been used."
        },
        "individual_use": {
            "type": "boolean",
            "description": "Whether the coupon can be used individually or with other coupons."
        },
        "product_ids": {
            "type": ["array", "null"],
            "items": {
                "type": "integer"
            },
            "description": "The products to which the coupon applies."
        },
        "excluded_product_ids": {
            "type": ["array", "null"],
            "items": {
                "type": "integer"
            },
            "description": "The products excluded from the coupon."
        },
        "usage_limit": {
            "type": "integer",
            "minimum": 1,
            "description": "The maximum number of times the coupon can be used."
        },
        "usage_limit_per_user": {
            "type": ["integer", "null"],
            "minimum": 1,
            "description": "The maximum number of times a user can use the coupon."
        },
        "limit_usage_to_x_items": {
            "type": ["integer", "null"],
            "minimum": 1,
            "description": "The maximum number of items the coupon can be applied to."
        },
        "free_shipping": {
            "type": "boolean",
            "description": "Whether the coupon grants free shipping."
        },
        "product_categories": {
            "type": ["array", "null"],
            "items": {
                "type": "string"
            },
            "description": "The categories to which the coupon applies."
        },
        "excluded_product_categories": {
            "type": ["array", "null"],
            "items": {
                "type": "string"
            },
            "description": "The categories excluded from the coupon."
        },
        "exclude_sale_items": {
            "type": "boolean",
            "description": "Whether the coupon applies to items on sale."
        },
        "minimum_amount": {
            "type": "number",
            "minimum": 0,
            "description": "The minimum purchase amount required to use the coupon."
        },
        "maximum_amount": {
            "type": "number",
            "minimum": 0,
            "description": "The maximum purchase amount for which the coupon applies."
        },
        "email_restrictions": {
            "type": ["array", "null"],
            "items": {
                "type": "string",
                "format": "email"
            },
            "description": "The email addresses restricted from using the coupon."
        },
        "used_by": {
            "type": ["array", "null"],
            "items": {
                "type": "string"
            },
            "description": "The users who have used the coupon."
        },
        "meta_data": {
            "type": ["array", "null"],
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "key": {"type": "string"},
                    "value": {"type": "string"}
                },
                "required": ["id", "key", "value"]
            },
            "description": "Additional metadata associated with the coupon."
        },
        "_links": {
            "type": ["object", "null"],
            "properties": {
                "self": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "href": {"type": "string", "format": "uri"}
                        },
                        "required": ["href"]
                    }
                },
                "collection": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "href": {"type": "string", "format": "uri"}
                        },
                        "required": ["href"]
                    }
                }
            },
            "description": "Links to the coupon's self and collection endpoints."
        }
    },
    "required": [
        "id", "code", "amount", "date_created", "date_created_gmt", "date_modified", "date_modified_gmt",
        "discount_type", "date_expires", "date_expires_gmt", "usage_count", "individual_use", "usage_limit",
        "free_shipping", "exclude_sale_items", "minimum_amount", "maximum_amount"
    ]
}
