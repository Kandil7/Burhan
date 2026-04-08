#!/usr/bin/env python3
"""Fix all bare except: clauses in src/ directory."""
import re
from pathlib import Path

FIXES = {
    'src/agents/seerah_agent.py': [
        ('        except:\n            self.embedding_model = None',
         '        except Exception as e:\n            logger.warning("seerah_agent.embedding_failed", error=str(e))\n            self.embedding_model = None'),
        ('        except:\n            self.vector_store = None\n            self.hybrid_searcher = None',
         '        except Exception as e:\n            logger.warning("seerah_agent.vector_store_failed", error=str(e))\n            self.vector_store = None\n            self.hybrid_searcher = None'),
        ('            except: self._llm_available = False',
         '            except Exception as e:\n                logger.warning("seerah_agent.llm_failed", error=str(e))\n                self._llm_available = False'),
        ('        except: return p[:300]',
         '        except Exception as e:\n            logger.warning("seerah_agent.generation_failed", error=str(e))\n            return p[:300]'),
    ],
    'src/agents/islamic_history_agent.py': [
        ('        except: self.embedding_model = None',
         '        except Exception as e:\n            logger.warning("islamic_history_agent.embedding_failed", error=str(e))\n            self.embedding_model = None'),
        ('        except:\n            self.vector_store = None\n            self.hybrid_searcher = None',
         '        except Exception as e:\n            logger.warning("islamic_history_agent.vector_store_failed", error=str(e))\n            self.vector_store = None\n            self.hybrid_searcher = None'),
        ('            except: self._llm_available = False',
         '            except Exception as e:\n                logger.warning("islamic_history_agent.llm_failed", error=str(e))\n                self._llm_available = False'),
        ('        except: return p[:300]',
         '        except Exception as e:\n            logger.warning("islamic_history_agent.generation_failed", error=str(e))\n            return p[:300]'),
    ],
    'src/agents/fiqh_usul_agent.py': [
        ('        except: self.embedding_model = None',
         '        except Exception as e:\n            logger.warning("fiqh_usul_agent.embedding_failed", error=str(e))\n            self.embedding_model = None'),
        ('        except:\n            self.vector_store = None\n            self.hybrid_searcher = None',
         '        except Exception as e:\n            logger.warning("fiqh_usul_agent.vector_store_failed", error=str(e))\n            self.vector_store = None\n            self.hybrid_searcher = None'),
        ('            except: self._llm_available = False',
         '            except Exception as e:\n                logger.warning("fiqh_usul_agent.llm_failed", error=str(e))\n                self._llm_available = False'),
        ('        except: return p[:300]',
         '        except Exception as e:\n            logger.warning("fiqh_usul_agent.generation_failed", error=str(e))\n            return p[:300]'),
    ],
    'src/agents/arabic_language_agent.py': [
        ('        except:\n            self.embedding_model = None',
         '        except Exception as e:\n            logger.warning("arabic_language_agent.embedding_failed", error=str(e))\n            self.embedding_model = None'),
        ('        except:\n            self.vector_store = None\n            self.hybrid_searcher = None',
         '        except Exception as e:\n            logger.warning("arabic_language_agent.vector_store_failed", error=str(e))\n            self.vector_store = None\n            self.hybrid_searcher = None'),
        ('            except: self._llm_available = False',
         '            except Exception as e:\n                logger.warning("arabic_language_agent.llm_failed", error=str(e))\n                self._llm_available = False'),
        ('        except: return p[:300]',
         '        except Exception as e:\n            logger.warning("arabic_language_agent.generation_failed", error=str(e))\n            return p[:300]'),
    ],
    'src/agents/tafsir_agent.py': [
        ('            except:\n                self.tafsir_retrieval = None',
         '            except Exception as e:\n                logger.warning("tafsir_agent.retrieval_failed", error=str(e))\n                self.tafsir_retrieval = None'),
        ('        except:\n            return passage[:300]',
         '        except Exception as e:\n            logger.warning("tafsir_agent.generation_failed", error=str(e))\n            return passage[:300]'),
    ],
}

def fix_file(filepath, replacements):
    p = Path(filepath)
    if not p.exists():
        print(f"⏭️  Not found: {filepath}")
        return 0
    
    content = p.read_text(encoding='utf-8')
    original = content
    count = 0
    
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            count += 1
            print(f"  ✅ Fixed: {old[:50]}...")
        else:
            print(f"  ⚠️  Not found: {old[:50]}...")
    
    if count > 0:
        p.write_text(content, encoding='utf-8')
        print(f"✅ {filepath}: {count} fixes applied")
    
    return count

total = 0
for filepath, replacements in FIXES.items():
    total += fix_file(filepath, replacements)

print(f"\n🎉 Total fixes: {total}")
