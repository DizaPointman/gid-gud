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







"""    if final_cat[0] in old_categories:
        if final_cat[1] in old_categories[final_cat[0]]:
            if final_cat[2] in old_categories[final_cat[0]][final_cat[1]]:
                return True
            else:
                new_sub_sub = str(final_cat[2])
                old_categories[final_cat[0]][final_cat[1]] = {'uncategorized': [], new_sub_sub: []}
                user.categories = old_categories
        else:
            new_sub = str(final_cat[1])
            old_categories[final_cat[0]] = {'uncategorized': [], new_sub: []}
            user.categories = old_categories
    else:
        new_cat = str(final_cat[0])
        old_categories = {'uncategorized': [], new_cat: []}
        if final_cat[1] in old_categories[final_cat[0]]:
            if final_cat[2] in old_categories[final_cat[0]][final_cat[1]]:
                return True
            else:
                new_sub_sub = str(final_cat[2])
                old_categories[final_cat[0]][final_cat[1]] = {'uncategorized': [], new_sub_sub: []}
                user.categories = old_categories
        else:
            new_sub = str(final_cat[1])
            old_categories[final_cat[0]] = {'uncategorized': [], new_sub: []}
            if final_cat[2] in old_categories[final_cat[0]][final_cat[1]]:
                user.categories = old_categories
            else:
                new_sub_sub = str(final_cat[2])
                old_categories[final_cat[0]][final_cat[1]] = {'uncategorized': [], new_sub_sub: []}
                user.categories = old_categories"""