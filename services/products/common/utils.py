from typing import Dict, List

from django.core.cache import cache
from django.core.paginator import Paginator, Page

from api.models import Category, Tag


class CachedPaginator(Paginator):
    """A paginator that caches the results on a page by page basis."""

    def __init__(self, object_list, per_page, cache_key, cache_timeout=300, orphans=0, allow_empty_first_page=True):
        super(CachedPaginator, self).__init__(object_list, per_page, orphans, allow_empty_first_page)
        self.cache_key = cache_key
        self.cache_timeout = cache_timeout

    def page(self, number):
        """
        Returns a Page object for the given 1-based page number.

        This will attempt to pull the results out of the cache first, based on
        the number of objects per page and the requested page number. If not
        found in the cache, it will pull a fresh list and then cache that
        result.
        """
        number = self.validate_number(number)
        cached_object_list = cache.get(self.build_cache_key(number), None)

        if cached_object_list is not None:
            page = Page(cached_object_list, number, self)
        else:
            page = super(CachedPaginator, self).page(number)
            # Since the results are fresh, cache it.
            cache.set(self.build_cache_key(number), page.object_list, self.cache_timeout)

        return page

    def build_cache_key(self, page_number):
        """Appends the relevant pagination bits to the cache key."""
        return "%s:%s:%s" % (self.cache_key, self.per_page, page_number)


def get_tree(category: Category, depth=10) -> Dict:
    """
    get sub tree at specific depth from a category as root node

    Args:
        category (Category): the root node
        depth (int, optional): the depth of sub tree. Defaults to 10.

    Returns:
        Dict: a category sub tree
    """
    if depth < 1:
        return []
    return {
        "category": category,
        "children": [get_tree(children, depth - 1) for children in category.children.all()],
    }


from collections import deque


def flatten_subtree(tree):
    items = []
    queue = deque()
    queue.append(tree)

    while queue:
        node = queue.popleft()
        for child in node["children"]:
            queue.append(child)
        items.append(node["category"])

    return items


def get_tags(tags: List) -> list:
    """
    check if tags exists in product db

    Args:
        tags (List): list of tags

    Returns:
        list: original list of tags ids
    """
    tag_ids = []
    for tag in tags:
        try:
            tag = Tag.objects.get(name=tag)
            tag_ids.append(tag.pk)
        except Tag.DoesNotExist as e:
            raise e
    return tag_ids
