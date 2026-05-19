"""
TCGIS - Elasticsearch Client
Advanced search and indexing
"""

import os
from typing import List, Dict, Any, Optional

from elasticsearch import AsyncElasticsearch


ELASTICSEARCH_URL = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
INDEX_NAME = os.getenv('ELASTICSEARCH_INDEX', 'groups')


class ElasticsearchClient:
    """عميل Elasticsearch للبحث المتقدم"""
    
    def __init__(self):
        self.client: Optional[AsyncElasticsearch] = None
    
    async def connect(self):
        """إنشاء الاتصال"""
        self.client = AsyncElasticsearch([ELASTICSEARCH_URL])
        await self._create_index_if_not_exists()
        print("✅ Elasticsearch connected successfully")
    
    async def disconnect(self):
        """إغلاق الاتصال"""
        if self.client:
            await self.client.close()
            print("✅ Elasticsearch disconnected")
    
    async def _create_index_if_not_exists(self):
        """إنشاء الفهرس إذا لم يكن موجوداً"""
        exists = await self.client.indices.exists(index=INDEX_NAME)
        if not exists:
            await self.client.indices.create(
                index=INDEX_NAME,
                body={
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                        "analysis": {
                            "analyzer": {
                                "arabic_analyzer": {
                                    "type": "custom",
                                    "tokenizer": "standard",
                                    "filter": [
                                        "lowercase",
                                        "arabic_normalization",
                                        "arabic_stemmer"
                                    ]
                                },
                                "english_analyzer": {
                                    "type": "custom",
                                    "tokenizer": "standard",
                                    "filter": [
                                        "lowercase",
                                        "english_stop",
                                        "english_stemmer"
                                    ]
                                }
                            }
                        }
                    },
                    "mappings": {
                        "properties": {
                            "id": {"type": "long"},
                            "telegram_id": {"type": "long"},
                            "username": {"type": "keyword"},
                            "title": {
                                "type": "text",
                                "analyzer": "arabic_analyzer",
                                "fields": {
                                    "english": {
                                        "type": "text",
                                        "analyzer": "english_analyzer"
                                    },
                                    "keyword": {"type": "keyword"}
                                }
                            },
                            "title_ar": {"type": "text", "analyzer": "arabic_analyzer"},
                            "description": {"type": "text", "analyzer": "arabic_analyzer"},
                            "description_ar": {"type": "text", "analyzer": "arabic_analyzer"},
                            "country_code": {"type": "keyword"},
                            "country_name": {"type": "keyword"},
                            "category": {"type": "keyword"},
                            "subcategory": {"type": "keyword"},
                            "language": {"type": "keyword"},
                            "member_count": {"type": "integer"},
                            "quality_score": {"type": "integer"},
                            "activity_score": {"type": "integer"},
                            "status": {"type": "keyword"},
                            "is_verified": {"type": "boolean"},
                            "is_featured": {"type": "boolean"},
                            "keywords": {"type": "keyword"},
                            "tags": {"type": "keyword"},
                            "discovered_at": {"type": "date"},
                            "last_activity_at": {"type": "date"},
                            "suggest": {
                                "type": "completion"
                            }
                        }
                    }
                }
            )
            print(f"✅ Created index: {INDEX_NAME}")
    
    async def index_group(self, group: Dict[str, Any]) -> bool:
        """فهرسة مجموعة"""
        try:
            # إضافة suggest للإكمال التلقائي
            group['suggest'] = {
                "input": [
                    group.get('title', ''),
                    group.get('title_ar', ''),
                    group.get('username', '')
                ],
                "weight": group.get('member_count', 0)
            }
            
            await self.client.index(
                index=INDEX_NAME,
                id=str(group['id']),
                document=group
            )
            return True
        except Exception as e:
            print(f"❌ Error indexing group: {e}")
            return False
    
    async def bulk_index_groups(self, groups: List[Dict[str, Any]]) -> Dict:
        """فهرسة مجموعة بالجملة"""
        from elasticsearch.helpers import async_bulk
        
        actions = [
            {
                "_index": INDEX_NAME,
                "_id": str(group['id']),
                "_source": {
                    **group,
                    "suggest": {
                        "input": [
                            group.get('title', ''),
                            group.get('title_ar', ''),
                            group.get('username', '')
                        ],
                        "weight": group.get('member_count', 0)
                    }
                }
            }
            for group in groups
        ]
        
        success, errors = await async_bulk(self.client, actions)
        return {"success": success, "errors": errors}
    
    async def search_groups(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "relevance",
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        البحث المتقدم في المجموعات
        """
        must_clauses = []
        
        # البحث النصي
        if query:
            must_clauses.append({
                "multi_match": {
                    "query": query,
                    "fields": [
                        "title^3",
                        "title_ar^3",
                        "title.english^2",
                        "description^2",
                        "description_ar^2",
                        "keywords^2",
                        "tags",
                        "username"
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })
        
        # الفلاتر
        filter_clauses = []
        if filters:
            if filters.get('country_code'):
                filter_clauses.append({"term": {"country_code": filters['country_code']}})
            if filters.get('category'):
                filter_clauses.append({"term": {"category": filters['category']}})
            if filters.get('language'):
                filter_clauses.append({"term": {"language": filters['language']}})
            if filters.get('status'):
                filter_clauses.append({"term": {"status": filters['status']}})
            if filters.get('is_verified') is not None:
                filter_clauses.append({"term": {"is_verified": filters['is_verified']}})
            if filters.get('min_members'):
                filter_clauses.append({"range": {"member_count": {"gte": filters['min_members']}}})
            if filters.get('max_members'):
                filter_clauses.append({"range": {"member_count": {"lte": filters['max_members']}}})
            if filters.get('min_quality'):
                filter_clauses.append({"range": {"quality_score": {"gte": filters['min_quality']}}})
        
        # الترتيب
        sort_options = {
            "relevance": [{"_score": "desc"}],
            "members": [{"member_count": "desc"}],
            "quality": [{"quality_score": "desc"}, {"_score": "desc"}],
            "activity": [{"activity_score": "desc"}],
            "newest": [{"discovered_at": "desc"}]
        }
        
        from_offset = (page - 1) * per_page
        
        search_body = {
            "query": {
                "bool": {
                    "must": must_clauses,
                    "filter": filter_clauses
                }
            },
            "sort": sort_options.get(sort_by, sort_options["relevance"]),
            "from": from_offset,
            "size": per_page,
            "highlight": {
                "fields": {
                    "title": {},
                    "title_ar": {},
                    "description": {},
                    "description_ar": {}
                }
            },
            "aggs": {
                "by_country": {
                    "terms": {"field": "country_code", "size": 10}
                },
                "by_category": {
                    "terms": {"field": "category", "size": 20}
                },
                "by_language": {
                    "terms": {"field": "language", "size": 10}
                },
                "member_ranges": {
                    "range": {
                        "field": "member_count",
                        "ranges": [
                            {"to": 100, "key": "small"},
                            {"from": 100, "to": 1000, "key": "medium"},
                            {"from": 1000, "to": 10000, "key": "large"},
                            {"from": 10000, "key": "huge"}
                        ]
                    }
                }
            }
        }
        
        response = await self.client.search(
            index=INDEX_NAME,
            body=search_body
        )
        
        hits = response['hits']['hits']
        total = response['hits']['total']['value']
        
        results = []
        for hit in hits:
            source = hit['_source']
            source['score'] = hit['_score']
            source['highlights'] = hit.get('highlight', {})
            results.append(source)
        
        return {
            "results": results,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
            "aggregations": response.get('aggregations', {})
        }
    
    async def autocomplete(self, prefix: str, size: int = 10) -> List[str]:
        """الإكمال التلقائي"""
        response = await self.client.search(
            index=INDEX_NAME,
            body={
                "suggest": {
                    "group-suggest": {
                        "prefix": prefix,
                        "completion": {
                            "field": "suggest",
                            "size": size,
                            "fuzzy": {"fuzziness": "AUTO"}
                        }
                    }
                }
            }
        )
        
        suggestions = response['suggest']['group-suggest'][0]['options']
        return [s['text'] for s in suggestions]
    
    async def delete_group(self, group_id: int) -> bool:
        """حذف مجموعة من الفهرس"""
        try:
            await self.client.delete(index=INDEX_NAME, id=str(group_id))
            return True
        except Exception:
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """إحصائيات الفهرس"""
        stats = await self.client.indices.stats(index=INDEX_NAME)
        return {
            "total_docs": stats['indices'][INDEX_NAME]['total']['docs']['count'],
            "size_in_bytes": stats['indices'][INDEX_NAME]['total']['store']['size_in_bytes']
        }


# Instance global
es_client = ElasticsearchClient()
