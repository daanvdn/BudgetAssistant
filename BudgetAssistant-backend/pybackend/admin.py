from django.contrib import admin

from pybackend.models import *
from pybackend.rules import RuleSetWrapper

admin.site.register(BankAccount)
admin.site.register(CustomUser)
admin.site.register(Transaction)
admin.site.register(Category)
admin.site.register(CategoryTree)
admin.site.register(BudgetTree)
admin.site.register(BudgetTreeNode)
admin.site.register(Counterparty)
admin.site.register(RuleSetWrapper)
admin.site.register(TreeNode)
