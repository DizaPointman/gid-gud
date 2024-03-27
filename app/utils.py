import copy

# utils.py

def categorize_gidgud(cat, sub_cat, sub_sub):
    if not cat:
        final_cat = ['uncategorized']
    if cat:
        final_cat = [str(cat)]
        if sub_cat:
            final_cat.append(str(sub_cat))
            if sub_sub:
                final_cat.append(str(sub_sub))
    return final_cat

def update_categories(user, final_cat: list, run_num):
    old_categories = copy.deepcopy(user.categories)
    """cat = final_cat[0]
    sub_cat = final_cat[1] or False
    sub_sub = final_cat[2] or False"""

    def check_if_existing_cat(new, old):
        if new in old:
            old = old[new]
            check_if_existing_cat(new, old)
        else:
            return old
        
    def cat_not_existing(cat, old):
        old[cat] = {'uncategorized': []}

        
    for cat in final_cat:
        old = check_if_existing_cat(cat, old_categories)
        if old:
            cat_not_existing(cat, old)
            return 

