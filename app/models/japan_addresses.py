from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator

class JP_Addresses(Model):
    id = fields.IntField(pk=True, index=True)
    postal_code = fields.CharField(max_length=50, null=True)
    jp_prefecture = fields.CharField(max_length=128, null=True)
    jp_municipality = fields.CharField(max_length=128, null=True)
    jp_town = fields.CharField(max_length=128, null=True)
    en_prefecture = fields.CharField(max_length=128, null=True)
    en_municipality = fields.CharField(max_length=128, null=True)
    en_town = fields.CharField(max_length=128, null=True)


    @staticmethod
    def get_full_jp_address(self) -> str:
        return self.jp_prefecture + ' ' + self.jp_municipality + ' ' + self.jp_town
    
    class Meta:
        table = "japan_addresses"
        ordering = ["id"]
    

