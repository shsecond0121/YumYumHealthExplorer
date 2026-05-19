import pygame
import sys
import os

# Windows 작업표시줄이 EXE 아이콘으로 그룹핑되도록 App User Model ID 설정
if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            'olbarom.yumyumhealthexplorer.v1')
    except Exception:
        pass

from game import Game


def _resource_path(filename):
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        # src/의 부모(프로젝트 루트)에서 assets/ 등을 찾음
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, filename)


def main():
    # 사운드 믹서를 pygame.init() 보다 먼저 초기화
    pygame.mixer.pre_init(22050, -16, 2, 256)
    pygame.init()

    # 창/작업표시줄 아이콘 설정 (PNG는 pygame이 안전하게 로드)
    try:
        icon = pygame.image.load(_resource_path('assets/icons/냠냠건강탐험대icon.png'))
        icon = pygame.transform.smoothscale(icon, (32, 32))
        pygame.display.set_icon(icon)
    except Exception as e:
        print(f"[main] 아이콘 로드 실패: {e}")

    screen = pygame.display.set_mode((800, 450))
    pygame.display.set_caption("냠냠건강탐험대")

    game = Game(screen)
    game.run()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
