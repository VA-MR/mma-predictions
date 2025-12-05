#!/usr/bin/env python3
"""
Скрипт для очистки имен бойцов от артефактов парсинга.
Удаляет слова "Победа", "Поражение", "Pound", методы побед и другие артефакты.
"""

import re
from database.db import Database
from database.models import Fighter

def clean_fighter_name(name: str) -> str:
    """
    Очистить имя бойца от артефактов парсинга.
    
    Args:
        name: Исходное имя с артефактами
        
    Returns:
        Очищенное имя
    """
    original = name
    
    # Список артефактов для удаления
    artifacts = [
        # Результаты боев
        r'\bПобеда\b',
        r'\bПоражение\b',
        r'\bWin\b',
        r'\bLoss\b',
        r'\bDraw\b',
        r'\bНичья\b',
        
        # Методы побед
        r'\bKO\b',
        r'\bTKO\b',
        r'\bSubmission\b',
        r'\bDecision\b',
        r'\bРЕШЕНИЕ\b',
        r'\bСАБ\b',
        r'\bUnanimous\b',
        r'\bSplit\b',
        r'\bMajority\b',
        r'\bPound\b',
        r'\bDQ\b',
        r'\bDisqualification\b',
        r'\bNo Contest\b',
        r'\bNC\b',
        
        # Детали остановки боя
        r'\bElbows from Back Mount\b',
        r'\bFlying Knee\b',
        r'\bKnee to the Body\b',
        r'\bRight Hand\b',
        r'\bLeft Hand\b',
        r'\bRight Hook\b',
        r'\bLeft Hook\b',
        r'\bBody Shot\b',
        r'\bHead Kick\b',
        r'\bStraight Right\b',
        r'\bStraight Left\b',
        r'\bStraight\b',
        r'\bPunches\b',
        r'\bKicks\b',
        r'\bKick\b',
        r'\bElbows\b',
        r'\bElbow\b',
        r'\bChoke\b',
        r'\bRight\b',
        r'\bLeft\b',
        r'\bCross\b',
        r'\bJab\b',
        r'\bHook\b',
        r'\bUppercut\b',
        r'\bKnee\b',
        r'\bDoctor Stoppage\b',
        r'\bCorner Stoppage\b',
        r'\bTechnical\b',
        r'\bRetirement\b',
        r'\bInjury\b',
        r'\bStoppage\b',
        r'\bTKO/KO\b',
        
        # Раунды
        r'\bRound\b',
        r'\bR\d+\b',
        
        # Другие артефакты
        r'\bArce\b',  # Часто встречается в начале
        r'\bвес\b',
        r'\bкг\b',
        r'\bRef\b',
        r'\bReferee\b',
        r'\bTD\b',
    ]
    
    # Удалить артефакты
    for artifact in artifacts:
        name = re.sub(artifact, '', name, flags=re.IGNORECASE)
    
    # Удалить лишние пробелы
    name = ' '.join(name.split())
    
    # Удалить ведущие/конечные пробелы
    name = name.strip()
    
    # Если имя стало пустым или слишком коротким, вернуть оригинал
    if len(name) < 3:
        return original
    
    return name


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
        cleaned_name = clean_fighter_name(fighter.name)
        
        if cleaned_name != fighter.name:
            fixed_count += 1
            
            if fixed_count <= 10:  # Показать первые 10 изменений
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
        print("Для сохранения запустите: python3 fix_fighter_names.py --apply")
    
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

