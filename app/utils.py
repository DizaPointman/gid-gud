import copy

# utils.py

def categorize_gidgud(cat, subcat, subsubcat):
    if not cat:
        final_cat = ['uncategorized']
    if cat:
        final_cat = [str(cat)]
        if subcat:
            final_cat.append(str(subcat))
            if subsubcat:
                final_cat.append(str(subsubcat))
    return final_cat

def update_categories(user, final_cat):
    old_categories = copy.deepcopy(user.categories)
    if final_cat[0] in old_categories:
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
                user.categories = old_categories