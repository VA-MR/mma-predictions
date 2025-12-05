#!/usr/bin/env python3
"""
Улучшенная версия очистки имен бойцов.
Использует умный подход - извлекает только имена (слова с заглавной буквы).
"""

import re
from database.db import Database
from database.models import Fighter

def extract_fighter_name(name: str) -> str:
    """
    Извлечь настоящее имя бойца из строки с артефактами.
    
    Логика:
    1. Разделить на слова
    2. Найти последовательность слов, которые выглядят как имя
       (начинаются с заглавной буквы, не содержат английских слов в нижнем регистре)
    3. Взять самую длинную последовательность
    
    Args:
        name: Исходное имя с артефактами
        
    Returns:
        Очищенное имя
    """
    original = name
    
    # Список английских и русских слов-артефактов (в нижнем регистре)
    artifacts = {
        # Английские
        'from', 'to', 'the', 'and', 'or', 'of', 'back', 'mount', 'body', 
        'head', 'hand', 'shot', 'kick', 'flying', 'spinning', 'wheel',
        'overhand', 'power', 'ground', 'pound', 'backfist', 'knee', 'knees',
        'leg', 'strikes', 'strike', 'eye', 'poke', 'top', 'position',
        # Русские
        'не', 'засчитан', 'de',  # de - французский предлог
    }
    
    # Разделить на слова
    words = name.split()
    
    # Найти последовательности слов, которые похожи на имена
    name_sequences = []
    current_sequence = []
    
    for word in words:
        word_lower = word.lower()
        
        # Проверка: слово выглядит как часть имени?
        is_name_part = (
            # Начинается с заглавной буквы
            word[0].isupper() and
            # Не является артефактом
            word_lower not in artifacts and
            # Длина больше 1 символа
            len(word) > 1 and
            # Не является однобуквенным артефактом
            word_lower != word  # Если слово полностью в нижнем регистре, это артефакт
        )
        
        # Специальная обработка для предлогов типа "де", "ван", "фон" - они могут быть частью имени
        if word_lower in ['де', 'ван', 'фон', 'да', 'ди', 'дос', 'das', 'van', 'von', 'de', 'da', 'di', 'dos']:
            # Если это предлог между именами, включить его
            if current_sequence:  # Есть имя до него
                current_sequence.append(word)
                continue
        
        if is_name_part:
            current_sequence.append(word)
        else:
            if current_sequence:
                name_sequences.append(' '.join(current_sequence))
                current_sequence = []
    
    # Добавить последнюю последовательность
    if current_sequence:
        name_sequences.append(' '.join(current_sequence))
    
    if not name_sequences:
        return original
    
    # Выбрать самую длинную последовательность (обычно это настоящее имя)
    best_name = max(name_sequences, key=len)
    
    # Проверка: имя должно быть минимум 3 символа
    if len(best_name) < 3:
        return original
    
    return best_name


def fix_all_fighter_names(dry_run: bool = True):
    """
    Исправить имена всех бойцов в базе данных.
    
    Args:
        dry_run: Если True, только показать изменения без сохранения
    """
    db = Database('mma_data.db')
    session = db.get_session()
    
    # Получить всех бойцов
    fighters = session.query(Fighter).all()
    
    fixed_count = 0
    skipped_count = 0
    
    print(f"Обработка {len(fighters)} бойцов...")
    print()
    
    for fighter in fighters:
        cleaned_name = extract_fighter_name(fighter.name)
        
        if cleaned_name != fighter.name:
            fixed_count += 1
            
            if fixed_count <= 20:  # Показать первые 20 изменений
                print(f"ID {fighter.id}:")
                print(f"  Было:  '{fighter.name}'")
                print(f"  Стало: '{cleaned_name}'")
                print()
            
            if not dry_run:
                fighter.name = cleaned_name
        else:
            skipped_count += 1
    
    print("=" * 60)
    print(f"Всего бойцов: {len(fighters)}")
    print(f"Будет исправлено: {fixed_count}")
    print(f"Без изменений: {skipped_count}")
    print("=" * 60)
    
    if not dry_run:
        session.commit()
        print("\n✅ Изменения сохранены в базу данных!")
    else:
        print("\n⚠️  Режим DRY RUN - изменения НЕ сохранены")
        print("Для сохранения запустите: python3 fix_fighter_names_v2.py --apply")
    
    session.close()


if __name__ == "__main__":
    import sys
    
    # Проверить аргументы
    apply_changes = "--apply" in sys.argv
    
    if apply_changes:
        print("🚀 ПРИМЕНЕНИЕ ИЗМЕНЕНИЙ К БАЗЕ ДАННЫХ")
        print()
        response = input("Вы уверены? (yes/no): ")
        if response.lower() != "yes":
            print("Отменено")
            sys.exit(0)
        print()
    else:
        print("🔍 РЕЖИМ ПРЕДВАРИТЕЛЬНОГО ПРОСМОТРА (DRY RUN)")
        print()
    
    fix_all_fighter_names(dry_run=not apply_changes)

