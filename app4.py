""" 🎲 المساعد العبقري للدومينو - إصدار العرّاف المطوّر 🔮 """

import streamlit as st
import streamlit.components.v1 as components
import copy
import hashlib
import math
import time
from collections import Counter, defaultdict
from game_engine.tiles import Tile, Direction, ALL_TILES
from game_engine.state import GameState, Pos, Move
from ai_engine.xray import XRayEngine
from ai_engine.mcts import MCTSEngine
from ai_engine.advisor import GeniusAdvisor
from ui.svg import SVGRenderer as SVG
from ui.helpers import show_message, format_move
from config import Config

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ═══════════════════════════════════════════════════════
# إعداد الصفحة والأنماط
# ═══════════════════════════════════════════════════════
st.set_page_config(page_title="🎲 دومينو العرّاف", page_icon="🔮", layout="wide")

st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#0a0a1a,#111128)}
#MainMenu,footer{visibility:hidden}
.stButton>button{border-radius:10px!important;font-weight:600!important}
.stButton>button:hover{transform:translateY(-2px)!important}
[data-testid="stMetric"]{background:rgba(255,255,255,.04);border-radius:10px;padding:14px;border:1px solid rgba(255,255,255,.08)}
.glow-card{background:linear-gradient(135deg,#1B5E20,#2E7D32);border-radius:14px;padding:18px;color:#fff;text-align:center;margin:10px 0;box-shadow:0 6px 25px rgba(46,125,50,.3)}
.oracle-card{background:linear-gradient(135deg,#311B92,#512DA8);border-radius:14px;padding:18px;color:#fff;margin:10px 0;border:1px solid #7E57C2;box-shadow:0 4px 20px rgba(81,45,168,.4)}
.partner-card{background:linear-gradient(135deg,#01579B,#0277BD);border-radius:14px;padding:18px;color:#fff;margin:10px 0;border:1px solid #29B6F6;box-shadow:0 4px 20px rgba(2,119,189,.4)}
.danger-card{border-radius:14px;padding:16px;color:#fff;margin:10px 0;text-align:center}
.pattern-card{background:linear-gradient(135deg,#4A148C,#7B1FA2);border-radius:14px;padding:16px;color:#fff;margin:8px 0;border:1px solid #CE93D8}
.neural-card{background:linear-gradient(135deg,#004D40,#00796B);border-radius:14px;padding:16px;color:#fff;margin:8px 0;border:1px solid #4DB6AC;box-shadow:0 4px 15px rgba(0,121,107,.3)}
.regret-card{background:linear-gradient(135deg,#BF360C,#E64A19);border-radius:14px;padding:16px;color:#fff;margin:8px 0;border:1px solid #FF8A65}
.tree-card{background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:14px;padding:16px;color:#fff;margin:10px 0;border:1px solid #00d2ff30}
.training-card{background:linear-gradient(135deg,#1A237E,#283593);border-radius:16px;padding:22px;color:#fff;margin:12px 0;border:2px solid #5C6BC0;box-shadow:0 6px 25px rgba(40,53,147,.4)}
.lesson-card{background:rgba(255,255,255,0.05);border-radius:12px;padding:16px;margin:8px 0;border:1px solid rgba(255,255,255,0.1)}
.cert-card{background:linear-gradient(135deg,#F9A825,#FFD54F);border-radius:18px;padding:30px;color:#1a1a2e;text-align:center;margin:20px 0;border:3px solid #FFC107;box-shadow:0 8px 30px rgba(249,168,37,.4)}
.cache-badge{display:inline-block;background:#00C853;color:#fff;padding:2px 10px;border-radius:20px;font-size:12px;margin-right:8px}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# دوال مساعدة آمنة
# ═══════════════════════════════════════════════════════
def safe_ends(gs):
    if gs.board.is_empty:
        return []
    try:
        raw = gs.board.ends
        if raw is None:
            return []
        if isinstance(raw, (list, tuple)):
            return list(raw)
        if isinstance(raw, set):
            return sorted(list(raw))
        if isinstance(raw, int):
            return [raw]
        return list(raw)
    except Exception:
        return []


def safe_float(val, default=0.0):
    if val is None:
        return default
    try:
        result = float(val)
        if math.isnan(result) or math.isinf(result):
            return default
        return result
    except (TypeError, ValueError):
        return default


def safe_int(val, default=0):
    if val is None:
        return default
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def safe_str(val, default='?'):
    if val is None:
        return default
    try:
        return str(val)
    except Exception:
        return default


# ═══════════════════════════════════════════════════════
# 🧠 الأنظمة الذكية
# ═══════════════════════════════════════════════════════

class PatternAnalyzer:
    def __init__(self, gs):
        self.gs = gs

    def analyze_player(self, pos):
        player = self.gs.players[pos]
        played = player.played
        passed = player.passed_on

        profile = {
            'style': 'مجهول',
            'icon': '❓',
            'traits': [],
            'aggression': 50,
            'doubles_early': False,
            'lock_tendency': 0,
            'favorite_numbers': [],
            'weak_numbers': list(passed),
            'confidence': 0,
            'avg_tile_value': 0,
            'risk_to_us': 50,
        }

        if not played and not passed:
            profile['traits'].append("لم يكشف أوراقه بعد")
            return profile

        total_value = 0
        doubles_count = 0
        early_doubles = 0
        high_tiles = 0

        for i, t in enumerate(played):
            total_value += t.total
            if t.is_double:
                doubles_count += 1
                if i < 3:
                    early_doubles += 1
            if t.total >= 8:
                high_tiles += 1

        num_freq = Counter()
        for t in played:
            num_freq[t.a] += 1
            if not t.is_double:
                num_freq[t.b] += 1

        if num_freq:
            profile['favorite_numbers'] = [n for n, _ in num_freq.most_common(3)]

        if played:
            profile['avg_tile_value'] = total_value / len(played)
            profile['aggression'] = min(100, int(profile['avg_tile_value'] * 9))

            if early_doubles > 0:
                profile['doubles_early'] = True
                profile['aggression'] += 15
                profile['traits'].append("يتخلص من الدبل مبكراً ♦️")

            if high_tiles > len(played) * 0.6:
                profile['traits'].append("يفضل الأحجار الثقيلة 💪")
                profile['aggression'] += 10

            if high_tiles < len(played) * 0.3 and len(played) >= 3:
                profile['traits'].append("يلعب بحذر وتدرج 🐢")
                profile['aggression'] -= 10

        if passed:
            profile['traits'].append(f"لا يملك: {', '.join(map(str, sorted(passed)))}")
            if len(passed) >= 3:
                profile['traits'].append("مكشوف بشدة! 👁️")
            if len(passed) >= 4:
                profile['traits'].append("شبه محاصر 🚨")

        if played:
            same_num_plays = 0
            for t in played:
                if t.is_double:
                    same_num_plays += 1
            profile['lock_tendency'] = min(100, int(same_num_plays / max(1, len(played)) * 150))

        remaining = self.gs.players[pos].count
        if remaining <= 2 and pos in [Pos.RIGHT, Pos.LEFT]:
            profile['risk_to_us'] = 85
            profile['traits'].append(f"⚠️ قريب من الفوز ({remaining} أحجار)")
        elif remaining <= 1:
            profile['risk_to_us'] = 95
            profile['traits'].append("🚨 حجر واحد فقط!")

        agg = min(100, max(0, profile['aggression']))
        profile['aggression'] = agg

        if agg >= 70:
            profile['style'] = 'هجومي'
            profile['icon'] = '⚔️'
        elif agg >= 40:
            profile['style'] = 'متوازن'
            profile['icon'] = '⚖️'
        else:
            profile['style'] = 'دفاعي'
            profile['icon'] = '🛡️'

        if profile['lock_tendency'] >= 50:
            profile['style'] += ' / قفّال'
            profile['icon'] = '🔒'
            profile['traits'].append("يميل للقفل 🔒")

        profile['confidence'] = min(100, (len(played) + len(passed)) * 12)

        return profile

    def analyze_all(self):
        result = {}
        for pos in [Pos.RIGHT, Pos.PARTNER, Pos.LEFT]:
            result[pos] = self.analyze_player(pos)
        return result


class DangerMeter:
    def __init__(self, gs):
        self.gs = gs

    def calculate(self):
        danger = 45
        warnings = []

        for pos in [Pos.RIGHT, Pos.LEFT]:
            count = self.gs.players[pos].count
            if count <= 1:
                danger += 30
                warnings.append(f"🚨 {pos.label} عنده حجر واحد فقط!")
            elif count <= 2:
                danger += 20
                warnings.append(f"⚠️ {pos.label} عنده {count} حجر!")
            elif count <= 3:
                danger += 8
                warnings.append(f"🔔 {pos.label} عنده {count} أحجار")

        my_count = len(self.gs.my_hand)
        if my_count >= 6:
            danger += 12
            warnings.append(f"😟 لديك {my_count} أحجار!")
        elif my_count >= 5:
            danger += 6

        partner_count = self.gs.players[Pos.PARTNER].count
        if partner_count <= 1:
            danger -= 25
            warnings.append(f"✅ شريكك على وشك الفوز! ({partner_count} حجر)")
        elif partner_count <= 2:
            danger -= 12
            warnings.append(f"🟢 شريكك قريب ({partner_count} حجر)")

        ends_list = safe_ends(self.gs)

        if ends_list:
            can_play = sum(
                1 for t in self.gs.my_hand
                if t.a in ends_list or t.b in ends_list
            )
            if can_play == 0:
                danger += 25
                warnings.append("🚨 لا تملك أحجاراً تركب!")
            elif can_play == 1:
                danger += 12
                warnings.append("⚠️ حجر واحد فقط يركب!")

            if len(ends_list) >= 2:
                if ends_list[0] == ends_list[1]:
                    danger += 15
                    warnings.append(f"🔒 طرفا الطاولة = {ends_list[0]}! خطر قفل!")

        if self.gs.passes >= 2:
            danger += 8
            warnings.append("📊 تراكم الدق - اللعبة ضيقة")

        if self.gs.passes >= 3:
            danger += 10
            warnings.append("🔒 القفل وشيك!")

        my_weight = sum(t.total for t in self.gs.my_hand)
        if my_weight >= 30:
            danger += 8
            warnings.append(f"💰 أحجارك ثقيلة ({my_weight} نقطة)")

        danger = max(0, min(100, danger))

        if danger < 25:
            level = "آمن 😊"
            color = "#4CAF50"
            emoji = "🟢"
        elif danger < 50:
            level = "حذر 🤔"
            color = "#FFC107"
            emoji = "🟡"
        elif danger < 75:
            level = "خطر ⚠️"
            color = "#FF9800"
            emoji = "🟠"
        else:
            level = "حرج! 🔴"
            color = "#F44336"
            emoji = "🔴"

        return {
            'score': danger,
            'level': level,
            'color': color,
            'emoji': emoji,
            'warnings': warnings,
        }


class RegretTracker:
    @staticmethod
    def record(move_label, win_rate, all_moves_data):
        entry = {
            'move': safe_str(move_label),
            'win_rate': safe_float(win_rate, 0.5),
            'best_available': None,
            'best_win_rate': 0.0,
            'regret': 0.0,
            'timestamp': time.time(),
        }

        if all_moves_data:
            # 🛠️ الإصلاح الأول: قراءة المفتاح win_pct (كنسبة مئوية) بدلاً من win_rate (كنص)
            best = max(all_moves_data, key=lambda x: safe_float(x.get('win_pct', 0)))
            # 🛠️ الإصلاح الثاني: قراءة اسم الحركة من المفتاح move بدلاً من label الوهمي
            entry['best_available'] = safe_str(best.get('move', '?'))
            entry['best_win_rate'] = safe_float(best.get('win_pct', 0))
            entry['regret'] = max(0.0, entry['best_win_rate'] - entry['win_rate'])

        return entry

    @staticmethod
    def summary(history):
        if not history:
            return None

        total_regret = sum(safe_float(e.get('regret', 0)) for e in history)
        worst = max(history, key=lambda e: safe_float(e.get('regret', 0)))
        best = min(history, key=lambda e: safe_float(e.get('regret', 0)))
        avg_wr = sum(safe_float(e.get('win_rate', 0.5)) for e in history) / len(history)
        perfect = sum(1 for e in history if safe_float(e.get('regret', 0)) < 0.03)

        if total_regret < 0.05:
            grade = 'S+'
            grade_label = 'أسطوري! 🏆'
            grade_color = '#FFD700'
        elif total_regret < 0.15:
            grade = 'S'
            grade_label = 'ممتاز! ⭐'
            grade_color = '#4CAF50'
        elif total_regret < 0.30:
            grade = 'A'
            grade_label = 'جيد جداً 👍'
            grade_color = '#8BC34A'
        elif total_regret < 0.50:
            grade = 'B'
            grade_label = 'جيد 👌'
            grade_color = '#FFC107'
        elif total_regret < 0.80:
            grade = 'C'
            grade_label = 'مقبول 😐'
            grade_color = '#FF9800'
        else:
            grade = 'D'
            grade_label = 'يحتاج تحسين 📚'
            grade_color = '#F44336'

        return {
            'total_regret': total_regret,
            'avg_win_rate': avg_wr,
            'worst_decision': worst,
            'best_decision': best,
            'perfect_moves': perfect,
            'total_moves': len(history),
            'grade': grade,
            'grade_label': grade_label,
            'grade_color': grade_color,
        }


class DecisionTreeViz:
    @staticmethod
    def render_html(all_moves):
        if not all_moves:
            return "<p style='color:#888;text-align:center'>لا توجد بيانات</p>"

        clean_moves = []
        for md in all_moves:
            if md is None:
                continue
            if not isinstance(md, dict):
                continue
            clean_moves.append({
                # 🛠️ الإصلاح الثالث: قراءة البيانات بشكل صحيح لتعود الشجرة للعمل
                'win_rate': safe_float(md.get('win_pct', 0)),
                'label': safe_str(md.get('move', '?')),
                'visits': safe_int(md.get('visits', 0)),
            })

        if not clean_moves:
            return "<p style='color:#888;text-align:center'>لا توجد بيانات صالحة</p>"

        sorted_moves = sorted(clean_moves, key=lambda x: x['win_rate'], reverse=True)

        html = '''
        <div style="font-family:'Segoe UI',Arial;direction:rtl;padding:15px;">
            <div style="text-align:center;margin-bottom:25px;">
                <div style="display:inline-block;background:linear-gradient(135deg,#1a1a2e,#16213e);
                color:#00d2ff;padding:14px 28px;border-radius:50px;font-size:16px;
                border:2px solid #00d2ff;box-shadow:0 0 20px rgba(0,210,255,0.2);">
                    🎯 شجرة قراراتك المتاحة
                </div>
            </div>
            <div style="display:flex;justify-content:center;margin-bottom:15px;">
                <div style="width:2px;height:30px;background:linear-gradient(#00d2ff,#3a7bd5);"></div>
            </div>
            <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:14px;">
        '''

        for i, md in enumerate(sorted_moves[:8]):
            wr = md['win_rate']
            label = md['label']
            visits = md['visits']

            if wr >= 0.65:
                bg = 'linear-gradient(135deg,#1B5E20,#388E3C)'
                bc = '#4CAF50'
                glow = '0 0 15px rgba(76,175,80,.4)'
            elif wr >= 0.50:
                bg = 'linear-gradient(135deg,#33691E,#689F38)'
                bc = '#8BC34A'
                glow = '0 0 10px rgba(139,195,74,.3)'
            elif wr >= 0.40:
                bg = 'linear-gradient(135deg,#E65100,#F57C00)'
                bc = '#FF9800'
                glow = '0 0 10px rgba(255,152,0,.3)'
            else:
                bg = 'linear-gradient(135deg,#B71C1C,#D32F2F)'
                bc = '#F44336'
                glow = '0 0 10px rgba(244,67,54,.3)'

            star = '⭐ الأفضل' if i == 0 else f'#{i+1}'
            bar_w = max(5, int(wr * 100))

            html += f'''
            <div style="background:{bg};border-radius:14px;padding:16px;min-width:140px;max-width:180px;
            text-align:center;color:#fff;border:2px solid {bc};box-shadow:{glow};
            transition:transform 0.2s;cursor:default;"
            onmouseover="this.style.transform='scale(1.05)'"
            onmouseout="this.style.transform='scale(1)'">
                <div style="font-size:11px;color:rgba(255,255,255,0.8);font-weight:bold;">{star}</div>
                <div style="font-size:18px;font-weight:bold;margin:8px 0;">{label}</div>
                <div style="background:rgba(0,0,0,0.3);border-radius:8px;height:8px;margin:8px 0;overflow:hidden;">
                    <div style="background:{bc};height:100%;width:{bar_w}%;border-radius:8px;
                    transition:width 0.5s;"></div>
                </div>
                <div style="font-size:22px;font-weight:bold;">{wr:.0%}</div>
                <div style="font-size:10px;color:rgba(255,255,255,0.5);margin-top:4px;">
                    📊 {visits} محاكاة
                </div>
            </div>
            '''

        html += '''
            </div>
            <div style="text-align:center;margin-top:20px;font-size:12px;color:#666;">
                🟢 أخضر = مرتفع الفوز &nbsp; 🟡 أصفر = متوسط &nbsp; 🔴 أحمر = منخفض
            </div>
        </div>
        '''
        return html


class SmartCache:
    @staticmethod
    def board_hash(gs):
        parts = []
        try:
            for t in sorted(gs.board.tiles_on_table, key=lambda x: (x.a, x.b)):
                parts.append(f"{t.a}{t.b}")
        except Exception:
            parts.append("board_err")
        try:
            for t in sorted(gs.my_hand, key=lambda x: (x.a, x.b)):
                parts.append(f"h{t.a}{t.b}")
        except Exception:
            parts.append("hand_err")
        parts.append(f"t{gs.turn.value}")
        ends_list = safe_ends(gs)
        if ends_list:
            parts.append(f"e{''.join(map(str, ends_list))}")
        key = "_".join(parts)
        return hashlib.md5(key.encode()).hexdigest()[:16]

    @staticmethod
    def get(cache_dict, gs):
        if not isinstance(cache_dict, dict):
            return None
        h = SmartCache.board_hash(gs)
        entry = cache_dict.get(h, None)
        if entry is None:
            return None
        if not isinstance(entry, dict):
            return None
        result = entry.get('result', None)
        if result is None:
            return None
        if not isinstance(result, dict):
            return None
        if 'best_move' not in result:
            return None
        entry['hits'] = entry.get('hits', 0) + 1
        return entry

    @staticmethod
    def put(cache_dict, gs, result):
        if not isinstance(cache_dict, dict):
            return
        if not isinstance(result, dict):
            return
        h = SmartCache.board_hash(gs)
        cache_dict[h] = {
            'result': result,
            'timestamp': time.time(),
            'hits': 0,
        }
        if len(cache_dict) > 500:
            oldest = sorted(cache_dict.items(), key=lambda x: x[1].get('timestamp', 0))
            for k, _ in oldest[:100]:
                del cache_dict[k]

    @staticmethod
    def stats(cache_dict):
        if not isinstance(cache_dict, dict):
            return {'entries': 0, 'total_hits': 0}
        total = len(cache_dict)
        total_hits = 0
        for v in cache_dict.values():
            if isinstance(v, dict):
                total_hits += v.get('hits', 0)
        return {'entries': total, 'total_hits': total_hits}


class NeuralEvaluator:
    WEIGHTS = {
        'hand_size': -0.07,
        'hand_total': -0.004,
        'doubles_in_hand': -0.05,
        'playable_tiles': 0.11,
        'opponent_min_tiles': -0.14,
        'partner_tiles': -0.025,
        'board_control': 0.08,
        'passed_knowledge': 0.07,
        'number_diversity': 0.04,
        'endgame_weight': -0.003,
    }

    def __init__(self, gs):
        self.gs = gs

    def evaluate(self):
        features = self._extract_features()
        score = 0.50
        details = []
        for feat, value in features.items():
            w = self.WEIGHTS.get(feat, 0)
            contribution = w * value
            score += contribution
            if abs(contribution) > 0.02:
                if contribution > 0:
                    details.append(f"🟢 {self._feat_name(feat)}: +{contribution:.0%}")
                else:
                    details.append(f"🔴 {self._feat_name(feat)}: {contribution:.0%}")
        score = max(0.02, min(0.98, score))
        return score, features, details

    def _extract_features(self):
        gs = self.gs
        f = {}
        f['hand_size'] = len(gs.my_hand)
        f['hand_total'] = sum(t.total for t in gs.my_hand)
        f['doubles_in_hand'] = sum(1 for t in gs.my_hand if t.is_double)

        ends_list = safe_ends(gs)

        if ends_list:
            f['playable_tiles'] = sum(
                1 for t in gs.my_hand
                if t.a in ends_list or t.b in ends_list
            )
        else:
            f['playable_tiles'] = len(gs.my_hand)

        f['opponent_min_tiles'] = min(
            gs.players[Pos.RIGHT].count,
            gs.players[Pos.LEFT].count,
        )
        f['partner_tiles'] = gs.players[Pos.PARTNER].count

        if ends_list:
            my_nums = Counter()
            for t in gs.my_hand:
                my_nums[t.a] += 1
                my_nums[t.b] += 1
            f['board_control'] = sum(my_nums.get(e, 0) for e in ends_list)
        else:
            f['board_control'] = 0

        all_passed = set()
        for pos in [Pos.RIGHT, Pos.LEFT]:
            all_passed.update(gs.players[pos].passed_on)
        f['passed_knowledge'] = len(all_passed)

        nums = set()
        for t in gs.my_hand:
            nums.add(t.a)
            nums.add(t.b)
        f['number_diversity'] = len(nums)

        f['endgame_weight'] = f['hand_total']

        return f

    def _feat_name(self, feat):
        names = {
            'hand_size': 'حجم اليد',
            'hand_total': 'ثقل اليد',
            'doubles_in_hand': 'دبلات',
            'playable_tiles': 'أحجار قابلة للعب',
            'opponent_min_tiles': 'قرب الخصم من الفوز',
            'partner_tiles': 'أحجار الشريك',
            'board_control': 'السيطرة على الطاولة',
            'passed_knowledge': 'معرفة الخصم',
            'number_diversity': 'تنوع الأرقام',
            'endgame_weight': 'ثقل نهاية اللعبة',
        }
        return names.get(feat, feat)


# ═══════════════════════════════════════════════════════
# 🎓 بيانات دروس التدريب
# ═══════════════════════════════════════════════════════

TRAINING_LESSONS = [
    {
        'id': 1,
        'title': '♦️ متى تلعب الدبل؟',
        'difficulty': '⭐ مبتدئ',
        'icon': '♦️',
        'situation': (
            '**يدك:** [4|4] [4|6] [4|2] [6|1] [1|5] [5|3] [3|0]\n\n'
            '**الطاولة:** الأطراف هي **4** و **6**\n\n'
            '**السؤال:** ما أفضل حركة الآن؟'
        ),
        'options': [
            'العب [4|4] على الطرف 4 ♦️',
            'العب [4|6] على أحد الطرفين',
            'العب [6|1] على الطرف 6',
        ],
        'correct': 0,
        'explanation': (
            '✅ **الإجابة: العب [4|4]**\n\n'
            'لأنك تملك حجرين آخرين فيهما 4 → [4|6] و [4|2].\n'
            'التخلص من الدبل مبكراً آمن عندما تملك بدائل!\n\n'
            '💡 **القاعدة:** العب الدبل مبكراً إذا لديك أحجار بديلة من نفس الرقم.'
        ),
    },
    {
        'id': 2,
        'title': '🔒 فن القفل المتعمد',
        'difficulty': '⭐⭐ متوسط',
        'icon': '🔒',
        'situation': (
            '**يدك:** [5|5] [5|2] [2|3] [3|0] [0|0] [6|6] [6|1]\n\n'
            '**الطاولة:** الأطراف هي **5** و **3**\n\n'
            '**معلومة:** الخصم اليمين دق عندما كان الطرف **5**.\n\n'
            '**السؤال:** ما أفضل حركة لمحاصرة الخصم؟'
        ),
        'options': [
            'العب [5|5] على الطرف 5 (قفل الخمسات)',
            'العب [2|3] على الطرف 3',
            'العب [5|2] على الطرف 5',
        ],
        'correct': 0,
        'explanation': (
            '✅ **الإجابة: العب [5|5]**\n\n'
            'الخصم دق على 5 = ليس لديه خمسات!\n'
            'بلعب [5|5] تبقي الطرف 5 ولديك [5|2] لاحقاً.\n'
            'إذا جعلت الطرفين كلاهما 5 → الخصم يدق مجدداً!\n\n'
            '💡 **القاعدة:** احتكر الأرقام التي دق عليها الخصم!'
        ),
    },
    {
        'id': 3,
        'title': '👁️ قراءة دق الخصم',
        'difficulty': '⭐⭐ متوسط',
        'icon': '👁️',
        'situation': (
            '**الوضع:**\n'
            '- الخصم اليمين دق على **2** و **6**\n'
            '- الخصم اليسار دق على **0**\n\n'
            '**يدك:** [2|4] [6|3] [4|1] [1|5] [5|0]\n\n'
            '**الطاولة:** الأطراف هي **2** و **5**\n\n'
            '**السؤال:** ما الحركة التي تضغط على الخصوم أكثر؟'
        ),
        'options': [
            'العب [5|0] على الطرف 5 (يفتح 0 الذي لا يملكه اليسار)',
            'العب [2|4] على الطرف 2 (يفتح 4 بدل 2)',
            'العب [1|5] على الطرف 5',
        ],
        'correct': 0,
        'explanation': (
            '✅ **الإجابة: العب [5|0]**\n\n'
            'الخصم اليسار دق على 0 → بفتح الطرف 0 تحاصره!\n'
            'والخصم اليمين دق على 2 → الطرف الآخر 2 يحاصره أيضاً!\n'
            'النتيجة: الطرفان (2 و 0) كلاهما يحاصران خصماً!\n\n'
            '💡 **القاعدة:** اجعل أطراف الطاولة = أرقام دق عليها الخصوم!'
        ),
    },
    {
        'id': 4,
        'title': '🤝 التنسيق مع الشريك',
        'difficulty': '⭐⭐⭐ متقدم',
        'icon': '🤝',
        'situation': (
            '**الوضع:** شريكك لعب 3 حركات:\n'
            '- [3|5] ثم [3|1] ثم [3|6]\n'
            '- واضح أنه قوي في الرقم **3**\n\n'
            '**يدك:** [0|4] [4|2] [2|6] [6|6] [1|0]\n\n'
            '**الطاولة:** الأطراف هي **1** و **4**\n\n'
            '**السؤال:** كيف تساعد شريكك؟'
        ),
        'options': [
            'العب [1|0] على الطرف 1 (تفتح 0 وهو غير مفيد)',
            'العب [4|2] على الطرف 4 (تفتح 2)',
            'العب [0|4] على الطرف 4 ثم لاحقاً تفتح 3 لشريكك',
        ],
        'correct': 2,
        'explanation': (
            '✅ **الإجابة: العب [0|4] ثم خطط لفتح 3**\n\n'
            'بلعب [0|4] يصبح الطرف 0.\n'
            'لاحقاً تلعب [1|0] → يصبح الطرف 1.\n'
            'ثم شريكك يملك أحجار الـ 1 (لعب [3|1]) ويكمل!\n\n'
            'أو ابحث عن أي طريق يفتح الرقم 3 لشريكك.\n\n'
            '💡 **القاعدة:** ادعم شريكك بفتح أرقامه المفضلة!'
        ),
    },
    {
        'id': 5,
        'title': '💰 إدارة الأحجار الثقيلة',
        'difficulty': '⭐⭐⭐ متقدم',
        'icon': '💰',
        'situation': (
            '**يدك:** [6|6] [6|5] [5|4] [4|3] [3|0]\n\n'
            '**الطاولة:** الأطراف هي **6** و **4**\n\n'
            '**معلومة:** باقي لكل خصم 3 أحجار.\n'
            'اللعبة قد تُقفل قريباً.\n\n'
            '**السؤال:** ما الاستراتيجية الصحيحة؟'
        ),
        'options': [
            'العب [6|6] للتخلص من أثقل حجر (12 نقطة!)',
            'العب [6|5] على الطرف 6',
            'العب [4|3] على الطرف 4',
        ],
        'correct': 0,
        'explanation': (
            '✅ **الإجابة: العب [6|6]**\n\n'
            '[6|6] = 12 نقطة! أخطر حجر عند القفل.\n'
            'مع بقاء 3 أحجار لكل خصم، احتمال القفل عالٍ.\n'
            'تخلص منه الآن قبل فوات الأوان!\n\n'
            '💡 **القاعدة:** كلما اقتربت النهاية، '
            'أولوية التخلص من الثقيل تزداد!'
        ),
    },
]


# ═══════════════════════════════════════════════════════
# Session State
# ═══════════════════════════════════════════════════════
DEFAULTS = {
    'state': None,
    'phase': 'setup',
    'hand_input': [],
    'rec': None,
    'analysis': None,
    'advice': None,
    'log': [],
    'msg': '',
    'msg_type': 'info',
    'sims': 2000,
    'time_limit': 3.5,
    'show_xray': True,
    'pending_tile': None,
    'starter': Pos.ME,
    'regret_history': [],
    'smart_cache': {},
    'training_lesson': 0,
    'training_score': 0,
    'training_answers': {},
    'camera_photo': None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = copy.deepcopy(v) if isinstance(v, (list, dict)) else v


_NO_VALUE = object()


def S(k, v=_NO_VALUE):
    if v is not _NO_VALUE:
        st.session_state[k] = v
    return st.session_state.get(k)


def reset():
    for k, v in DEFAULTS.items():
        st.session_state[k] = copy.deepcopy(v) if isinstance(v, (list, dict)) else v


# ─── دوال مساعدة ───
def tile_key(t):
    if isinstance(t, Tile):
        return (min(t.a, t.b), max(t.a, t.b))
    return (min(t[0], t[1]), max(t[0], t[1]))


def get_remaining_tiles(gs):
    used = set()
    for t in gs.my_hand:
        used.add(tile_key(t))
    for t in gs.board.tiles_on_table:
        used.add(tile_key(t))
    return [t for t in ALL_TILES if tile_key(t) not in used]


def apply_opponent_move(gs, turn, tile, direction):
    m = Move(turn, tile, direction)
    count_before = gs.players[turn].count
    ok = gs.apply(m)
    if not ok:
        show_message("❌ فشل تطبيق الحركة داخلياً!", "error")
        return False
    if gs.players[turn].count == count_before:
        gs.players[turn].count -= 1
    if gs.players[turn].count <= 0 and not gs.game_over:
        gs.game_over = True
        gs.winner = turn
    S('log', S('log') + [format_move(m)])
    S('advice', None)
    S('pending_tile', None)
    dir_label = "⬅️ يسار" if direction == Direction.LEFT else "➡️ يمين"
    S('msg', f"✅ {turn.label} لعب [{tile.a}|{tile.b}] {dir_label}")
    S('msg_type', 'info')
    if gs.game_over:
        S('phase', 'over')
    S('state', gs)
    return True


def safe_render_tree(all_moves):
    try:
        if not all_moves:
            return
        tree_html = DecisionTreeViz.render_html(all_moves)
        if tree_html:
            components.html(tree_html, height=350, scrolling=True)
    except Exception:
        st.caption("⚠️ تعذّر عرض شجرة القرار")


def safe_analysis_chart(all_moves):
    try:
        if all_moves:
            SVG.analysis_chart(all_moves)
    except Exception:
        st.caption("⚠️ تعذّر عرض مخطط التحليل")


# ═══════════════════════════════════════════════════════
# الشريط الجانبي
# ═══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🧠 إعدادات العرّاف")
    st.markdown("---")
    S('sims', st.slider("عمق التفكير (محاكاة)", 500, 10000, S('sims'), 500))
    S('time_limit', st.slider("زمن الرؤية (ثواني)", 1.0, 10.0, S('time_limit'), 0.5))
    S('show_xray', st.checkbox("🔬 تفعيل X-Ray", S('show_xray')))
    st.markdown("---")

    cache_stats = SmartCache.stats(S('smart_cache'))
    if cache_stats['entries'] > 0:
        st.markdown(f"🧠 **الذاكرة الذكية:** {cache_stats['entries']} تحليل محفوظ")
        st.caption(f"استُخدمت {cache_stats['total_hits']} مرة")
        if st.button("🗑️ مسح الذاكرة", use_container_width=True):
            S('smart_cache', {})
            st.rerun()
        st.markdown("---")

    if st.button("🔄 لعبة جديدة", use_container_width=True, type="primary"):
        reset()
        st.rerun()

    st.markdown("---")
    if st.button("🎓 وضع التدريب", use_container_width=True):
        S('phase', 'training')
        S('training_lesson', 0)
        S('training_score', 0)
        S('training_answers', {})
        st.rerun()


# ═══════════════════════════════════════════════════════
# العنوان
# ═══════════════════════════════════════════════════════
st.markdown(
    '<h1 style="text-align:center;background:linear-gradient(90deg,#00d2ff,#3a7bd5);'
    '-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:2.2em">'
    '🔮 عـرّاف الـدومـيـنـو الذكـي</h1>',
    unsafe_allow_html=True,
)

phase = S('phase')
ALL_TILES_SORTED = sorted(ALL_TILES, key=lambda t: (t.a, t.b))


# ═══════════════════════════════════════════════════════
# 🎓 وضع التدريب
# ═══════════════════════════════════════════════════════
if phase == 'training':
    lesson_idx = S('training_lesson')
    total_lessons = len(TRAINING_LESSONS)

    st.markdown("### 🎓 أكاديمية الدومينو - تدريب تفاعلي")

    progress_val = lesson_idx / total_lessons
    st.progress(progress_val, text=f"التقدم: {lesson_idx}/{total_lessons} درس")

    score = S('training_score')
    st.markdown(f"**🏆 نقاطك: {score}/{total_lessons}**")

    if lesson_idx >= total_lessons:
        pct = (score / total_lessons) * 100
        if pct >= 80:
            grade_txt = "🏆 خبير دومينو!"
            grade_clr = "#FFD700"
        elif pct >= 60:
            grade_txt = "⭐ لاعب ممتاز"
            grade_clr = "#4CAF50"
        elif pct >= 40:
            grade_txt = "👍 لاعب جيد"
            grade_clr = "#FFC107"
        else:
            grade_txt = "📚 تحتاج مزيداً من التدريب"
            grade_clr = "#FF9800"

        st.markdown(f'''
        <div class="cert-card">
            <div style="font-size:50px;margin-bottom:10px;">🎓</div>
            <div style="font-size:24px;font-weight:bold;">شهادة إتمام التدريب</div>
            <div style="font-size:40px;font-weight:bold;margin:15px 0;color:{grade_clr};">{grade_txt}</div>
            <div style="font-size:18px;">النتيجة: {score}/{total_lessons} ({pct:.0f}%)</div>
            <div style="font-size:14px;margin-top:10px;color:#555;">
                أكملت جميع دروس أكاديمية الدومينو بنجاح!
            </div>
        </div>
        ''', unsafe_allow_html=True)

        c1_t, c2_t = st.columns(2)
        with c1_t:
            if st.button("🔁 أعد التدريب", use_container_width=True, type="primary"):
                S('training_lesson', 0)
                S('training_score', 0)
                S('training_answers', {})
                st.rerun()
        with c2_t:
            if st.button("🎮 العب مباراة حقيقية", use_container_width=True):
                S('phase', 'setup')
                st.rerun()

    else:
        lesson = TRAINING_LESSONS[lesson_idx]
        answers = S('training_answers')
        already_answered = lesson_idx in answers

        st.markdown(f'''
        <div class="training-card">
            <div style="font-size:12px;color:#B39DDB;">الدرس {lesson['id']} من {total_lessons} | {lesson['difficulty']}</div>
            <div style="font-size:24px;font-weight:bold;margin:10px 0;">{lesson['title']}</div>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown('<div class="lesson-card">', unsafe_allow_html=True)
        st.markdown("#### 📋 الموقف:")
        st.markdown(lesson['situation'])
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("#### 🤔 اختر إجابتك:")

        if not already_answered:
            for opt_i, opt_text in enumerate(lesson['options']):
                if st.button(
                    opt_text,
                    key=f"train_opt_{lesson_idx}_{opt_i}",
                    use_container_width=True,
                ):
                    is_correct = (opt_i == lesson['correct'])
                    answers[lesson_idx] = {
                        'chosen': opt_i,
                        'correct': is_correct,
                    }
                    S('training_answers', answers)
                    if is_correct:
                        S('training_score', S('training_score') + 1)
                    st.rerun()
        else:
            answer = answers[lesson_idx]
            chosen = answer['chosen']
            is_correct = answer['correct']

            for opt_i, opt_text in enumerate(lesson['options']):
                if opt_i == lesson['correct']:
                    st.success(f"✅ {opt_text}")
                elif opt_i == chosen and not is_correct:
                    st.error(f"❌ {opt_text} ← اختيارك")
                else:
                    st.markdown(f"⬜ {opt_text}")

            if is_correct:
                st.balloons()
                st.markdown(
                    '<div style="background:#1B5E20;color:#fff;padding:14px;border-radius:12px;'
                    'text-align:center;font-size:20px;margin:10px 0;">🎉 إجابة صحيحة!</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div style="background:#B71C1C;color:#fff;padding:14px;border-radius:12px;'
                    'text-align:center;font-size:20px;margin:10px 0;">😅 إجابة خاطئة</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("---")
            st.markdown("#### 📖 الشرح:")
            st.markdown(lesson['explanation'])

            st.markdown("---")
            if lesson_idx < total_lessons - 1:
                if st.button("➡️ الدرس التالي", use_container_width=True, type="primary"):
                    S('training_lesson', lesson_idx + 1)
                    st.rerun()
            else:
                if st.button("🏆 عرض النتيجة النهائية", use_container_width=True, type="primary"):
                    S('training_lesson', total_lessons)
                    st.rerun()


# ═══════════════════════════════════════════════════════
# 📝 الإعداد
# ═══════════════════════════════════════════════════════
elif phase == 'setup':
    st.markdown("### 📝 اختر أحجارك السبعة")

    with st.expander("📸 مساعد الكاميرا (صوّر أحجارك كمرجع)"):
        st.caption("صوّر أحجارك بالكاميرا ثم اختر من القائمة بالأسفل")
        try:
            photo = st.camera_input("📷 التقط صورة أحجارك", key="cam_setup")
            if photo is not None:
                S('camera_photo', photo)
                if HAS_PIL:
                    img = Image.open(photo)
                    st.image(img, caption="📸 صورة أحجارك - استخدمها كمرجع أثناء الاختيار", use_container_width=True)
                else:
                    st.image(photo, caption="📸 صورة أحجارك", use_container_width=True)
                st.success("✅ الصورة جاهزة! اختر أحجارك من الأزرار بالأسفل.")
        except Exception:
            st.info("📷 الكاميرا غير متاحة في هذا المتصفح. اختر يدوياً.")

    hand = S('hand_input')
    if hand:
        SVG.hand(hand, title="المختارة")
        st.success(f"✅ {len(hand)}/7")

    for row in range(0, len(ALL_TILES_SORTED), 7):
        cols = st.columns(7)
        for i, t in enumerate(ALL_TILES_SORTED[row:row + 7]):
            with cols[i]:
                sel = t in hand
                if st.button(
                    f"{'✅' if sel else ' '} [{t.a}|{t.b}]",
                    key=f"s_{t.a}_{t.b}",
                    use_container_width=True,
                    type="primary" if sel else "secondary",
                ):
                    h = S('hand_input')
                    if sel:
                        h.remove(t)
                    elif len(h) < 7:
                        h.append(t)
                    S('hand_input', h)
                    st.rerun()

    if len(hand) == 7:
        st.markdown("---")
        st.markdown("### 🎯 من يبدأ هذه الجولة؟")

        current_starter = S('starter')
        sc1, sc2, sc3, sc4 = st.columns(4)

        with sc1:
            if st.button(
                f"{'✅ ' if current_starter == Pos.ME else ''}🟢 أنا",
                key="str_me",
                use_container_width=True,
                type="primary" if current_starter == Pos.ME else "secondary",
            ):
                S('starter', Pos.ME)
                st.rerun()
        with sc2:
            if st.button(
                f"{'✅ ' if current_starter == Pos.RIGHT else ''}🔴 اليمين",
                key="str_right",
                use_container_width=True,
                type="primary" if current_starter == Pos.RIGHT else "secondary",
            ):
                S('starter', Pos.RIGHT)
                st.rerun()
        with sc3:
            if st.button(
                f"{'✅ ' if current_starter == Pos.PARTNER else ''}🔵 شريكي",
                key="str_partner",
                use_container_width=True,
                type="primary" if current_starter == Pos.PARTNER else "secondary",
            ):
                S('starter', Pos.PARTNER)
                st.rerun()
        with sc4:
            if st.button(
                f"{'✅ ' if current_starter == Pos.LEFT else ''}🟠 اليسار",
                key="str_left",
                use_container_width=True,
                type="primary" if current_starter == Pos.LEFT else "secondary",
            ):
                S('starter', Pos.LEFT)
                st.rerun()

        starter = S('starter')
        starter_name = {
            Pos.ME: "🟢 أنت",
            Pos.RIGHT: "🔴 اليمين (خصم)",
            Pos.PARTNER: "🔵 شريكك",
            Pos.LEFT: "🟠 اليسار (خصم)",
        }
        st.info(f"🎲 **{starter_name[starter]}** سيبدأ اللعبة")

        _, c_start, _ = st.columns([1, 2, 1])
        with c_start:
            if st.button("🎮 ابدأ السحر!", use_container_width=True, type="primary"):
                gs = GameState()
                gs.set_my_hand(hand.copy())
                gs.turn = starter
                S('state', gs)
                S('phase', 'playing')
                S('regret_history', [])
                S('msg', f"🎲 {starter_name[starter]} يبدأ اللعبة!")
                S('msg_type', 'info')
                st.rerun()


# ═══════════════════════════════════════════════════════
# 🎮 اللعب
# ═══════════════════════════════════════════════════════
elif phase == 'playing':
    gs: GameState = S('state')
    if not gs:
        st.error("خطأ!")
        st.stop()
    if S('msg'):
        show_message(S('msg'), S('msg_type'))

    # ─── مؤشر الخطر الحي ───
    if not gs.board.is_empty:
        dm = DangerMeter(gs)
        danger = dm.calculate()
        d_score = danger['score']
        d_color = danger['color']
        d_level = danger['level']
        d_emoji = danger['emoji']

        if d_score < 30:
            danger_bg = '#1B5E20,#388E3C'
        elif d_score < 60:
            danger_bg = '#E65100,#F57C00'
        else:
            danger_bg = '#B71C1C,#D32F2F'

        st.markdown(f'''
        <div class="danger-card" style="background:linear-gradient(135deg,{danger_bg});">
            <div style="display:flex;align-items:center;justify-content:center;gap:15px;">
                <div style="font-size:32px;">{d_emoji}</div>
                <div>
                    <div style="font-size:12px;opacity:0.8;">مؤشر الخطر الحي</div>
                    <div style="font-size:22px;font-weight:bold;">{d_level}</div>
                </div>
                <div style="flex:1;max-width:200px;">
                    <div style="background:rgba(0,0,0,0.3);border-radius:10px;height:14px;overflow:hidden;">
                        <div style="background:{d_color};height:100%;width:{d_score}%;border-radius:10px;
                        transition:width 0.5s;box-shadow:0 0 8px {d_color};"></div>
                    </div>
                </div>
                <div style="font-size:24px;font-weight:bold;">{d_score}%</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        if danger['warnings']:
            with st.expander(f"📋 تنبيهات ({len(danger['warnings'])})"):
                for w in danger['warnings']:
                    st.markdown(f"- {w}")

    st.markdown("### 🎯 الطاولة")
    SVG.board(gs.board, h=200)

    with st.expander("👥 اللاعبون", expanded=True):
        SVG.players(gs, w=700, h=380)

    st.markdown("---")
    turn = gs.turn

    # ═══════════════════════════════════
    # 🎯 دوري
    # ═══════════════════════════════════
    if turn == Pos.ME:
        valid = gs.valid_moves(Pos.ME)
        real = [m for m in valid if not m.is_pass]

        if gs.board.is_empty and not real:
            real = [Move(Pos.ME, t, Direction.LEFT) for t in gs.my_hand]

        st.markdown("### 🎯 دورك للتفكير والتخطيط!")

        # ─── التقييم العصبي السريع ───
        ne = NeuralEvaluator(gs)
        n_score, n_feats, n_details = ne.evaluate()
        if n_score >= 0.6:
            n_color = "#4CAF50"
            n_emoji = "😊"
        elif n_score >= 0.4:
            n_color = "#FFC107"
            n_emoji = "😐"
        else:
            n_color = "#F44336"
            n_emoji = "😟"

        st.markdown(f'''
        <div class="neural-card">
            <div style="display:flex;align-items:center;justify-content:space-between;">
                <div>
                    <div style="font-size:11px;color:#80CBC4;">🧠 التقييم العصبي الفوري</div>
                    <div style="font-size:20px;font-weight:bold;color:{n_color};">
                        وضعك: {n_score:.0%}
                    </div>
                </div>
                <div style="font-size:36px;">{n_emoji}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        if n_details:
            with st.expander("🔬 تفاصيل التقييم العصبي"):
                for d in n_details:
                    st.markdown(f"  {d}")

        # ─── أنظمة العراف ───
        xray = XRayEngine(gs)
        report = xray.xray_report()

        col_oracle, col_partner = st.columns(2)

        with col_oracle:
            next_enemy = Pos.RIGHT
            enemy_rep = report[next_enemy]
            threats = []
            ends_list = safe_ends(gs)
            if ends_list:
                for t, prob in enemy_rep['likely']:
                    if safe_float(prob) > 0.4 and (t.a in ends_list or t.b in ends_list):
                        threats.append((t, safe_float(prob)))
                for t in enemy_rep['certain']:
                    if t.a in ends_list or t.b in ends_list:
                        threats.append((t, 1.0))

            st.markdown('<div class="oracle-card">', unsafe_allow_html=True)
            st.markdown("#### 🔮 عين العرّاف (تنبؤ الخصم)")
            if gs.board.is_empty:
                st.write("الطاولة فارغة، العب براحتك!")
            elif threats:
                st.warning("⚠️ الخصم اليمين جاهز للعب!")
                for t, p in threats[:3]:
                    st.write(f"- يمتلك **{t}** بنسبة `{p:.0%}`")
            else:
                st.success("✅ الخصم اليمين ضعيف على الأطراف الحالية.")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_partner:
            partner_rep = report[Pos.PARTNER]
            partner_played = gs.players[Pos.PARTNER].played

            prefs = Counter()
            for t in partner_played:
                prefs[t.a] += 1
                if not t.is_double:
                    prefs[t.b] += 1
            for t in partner_rep['certain']:
                prefs[t.a] += 1
                prefs[t.b] += 1

            st.markdown('<div class="partner-card">', unsafe_allow_html=True)
            st.markdown("#### 🤝 بوصلة الشريك")
            if not prefs:
                st.write("شريكك لم يكشف أوراقه بعد.")
            else:
                best_nums = [
                    n for n, cnt in prefs.most_common(2)
                    if n not in gs.players[Pos.PARTNER].passed_on
                ]
                if best_nums:
                    st.success(f"🔵 شريكك قوي في: **{', '.join(map(str, best_nums))}**")
                    st.write("حاول فتح هذه الأطراف له.")
                else:
                    st.info("لم نحدد نقطة قوة واضحة بعد.")
            st.markdown('</div>', unsafe_allow_html=True)

        # ─── تحليل أنماط اللاعبين ───
        with st.expander("🎭 قراءة أنماط اللاعبين (Pattern Recognition)"):
            pa = PatternAnalyzer(gs)
            profiles = pa.analyze_all()

            pt1, pt2, pt3 = st.columns(3)
            for col_p, pos in zip([pt1, pt2, pt3], [Pos.RIGHT, Pos.PARTNER, Pos.LEFT]):
                with col_p:
                    p = profiles[pos]
                    is_enemy = pos in [Pos.RIGHT, Pos.LEFT]
                    border_clr = "#F44336" if is_enemy else "#2196F3"

                    if p['aggression'] > 60:
                        agg_color = '#F44336'
                    elif p['aggression'] > 35:
                        agg_color = '#FFC107'
                    else:
                        agg_color = '#4CAF50'

                    st.markdown(f'''
                    <div class="pattern-card" style="border-color:{border_clr};">
                        <div style="font-size:28px;">{p['icon']}</div>
                        <div style="font-size:14px;font-weight:bold;margin:6px 0;">{pos.label}</div>
                        <div style="font-size:18px;color:#CE93D8;font-weight:bold;">{p['style']}</div>
                        <div style="margin-top:8px;">
                            <div style="font-size:11px;color:#aaa;">عدوانية</div>
                            <div style="background:rgba(0,0,0,0.3);border-radius:6px;height:8px;overflow:hidden;margin:4px 0;">
                                <div style="background:{agg_color};
                                height:100%;width:{p['aggression']}%;border-radius:6px;"></div>
                            </div>
                        </div>
                        <div style="font-size:11px;color:#aaa;margin-top:4px;">
                            دقة التحليل: {p['confidence']}%
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)

                    if p['traits']:
                        for trait in p['traits'][:4]:
                            st.caption(f"  {trait}")
                    if p['favorite_numbers']:
                        st.caption(f"  🎯 أرقام مفضلة: {p['favorite_numbers']}")

        # ─── زر التحليل العميق ───
        col_btn, col_result = st.columns([1, 2])
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)

            cached = SmartCache.get(S('smart_cache'), gs)
            cache_label = ""
            if cached:
                cache_label = " (⚡ من الذاكرة)"

            if st.button(
                f"🧠 مشورة العبقري MCTS!{cache_label}",
                use_container_width=True,
                type="primary",
            ):
                if cached:
                    S('advice', cached['result'])
                    S('msg', '⚡ تم استرجاع التحليل من الذاكرة الذكية!')
                    S('msg_type', 'success')
                    st.rerun()
                else:
                    with st.spinner("⏳ العبقري يحلل ملايين الاحتمالات..."):
                        cfg = Config()
                        cfg.MCTS_SIMULATIONS = S('sims')
                        cfg.MCTS_TIME_LIMIT = S('time_limit')
                        advisor = GeniusAdvisor(gs, cfg)
                        advice = advisor.advise()
                        S('advice', advice)
                        SmartCache.put(S('smart_cache'), gs, advice)
                        st.rerun()

            if cached:
                st.markdown(
                    '<span class="cache-badge">⚡ ذاكرة</span>',
                    unsafe_allow_html=True,
                )

        with col_result:
            adv = S('advice')
            if adv and isinstance(adv, dict) and 'best_move' in adv:
                bm = adv['best_move']
                wr = safe_float(adv.get('win_rate', 0))
                exp = safe_str(adv.get('explanation', ''))
                if bm.is_pass:
                    txt = "دق 🚫"
                else:
                    d = "⬅️ يسار" if bm.direction == Direction.LEFT else "➡️ يمين"
                    txt = f"{bm.tile} {d}"
                if wr >= 0.6:
                    wr_color = "#4CAF50"
                elif wr >= 0.4:
                    wr_color = "#FFC107"
                else:
                    wr_color = "#F44336"
                st.markdown(f'''
                <div class="glow-card">
                    <div style="font-size:12px;color:#A5D6A7">🧠 قرار المحرك النهائي:</div>
                    <div style="font-size:24px;font-weight:bold;margin:8px 0">⭐ {txt}</div>
                    <div style="font-size:18px;color:{wr_color};margin:4px 0">احتمالية الفوز: {wr:.0%}</div>
                    <div style="font-size:13px;color:#C8E6C9;margin-top:6px">💡 {exp}</div>
                </div>
                ''', unsafe_allow_html=True)

                if adv.get('reasons'):
                    with st.expander("📝 أسرار هذه الحركة؟", expanded=True):
                        for r in adv['reasons']:
                            st.markdown(f"- {r}")

                all_moves = adv.get('all_moves')
                if all_moves:
                    with st.expander("🌳 شجرة القرار المرئية", expanded=True):
                        safe_render_tree(all_moves)

                    safe_analysis_chart(all_moves)

        # ─── X-Ray ───
        if S('show_xray'):
            with st.expander("🔬 كشف الأوراق (X-Ray) التفصيلي"):
                tabs = st.tabs([p.label for p in [Pos.RIGHT, Pos.PARTNER, Pos.LEFT]])
                for tab, pos in zip(tabs, [Pos.RIGHT, Pos.PARTNER, Pos.LEFT]):
                    with tab:
                        r = report[pos]
                        st.caption(f"أحجار: {r['count']} | مستحيل: {r['impossible_count']} حجر")
                        if r['cant_have']:
                            st.error(f"🚫 أرقام يفتقدها: {', '.join(map(str, r['cant_have']))}")
                        if r['certain']:
                            st.success(f"✅ أوراق مؤكدة: {', '.join(str(t) for t in r['certain'])}")
                        for tile, prob in r['likely'][:8]:
                            p_val = safe_float(prob)
                            if p_val < 0.01:
                                continue
                            lc1, lc2 = st.columns([1, 4])
                            with lc1:
                                st.write(f"**{tile}**")
                            with lc2:
                                st.progress(min(p_val, 1.0), text=f"{p_val:.0%}")

        # ─── أزرار اللعب ───
        st.markdown("#### 👇 نفذ حركتك:")
        if real:
            adv = S('advice')
            bcols = st.columns(min(len(real), 4))
            for i, m in enumerate(real):
                with bcols[i % len(bcols)]:
                    d = "⬅️" if m.direction == Direction.LEFT else "➡️"
                    is_rec = False
                    if adv and isinstance(adv, dict) and 'best_move' in adv:
                        bm = adv['best_move']
                        if not bm.is_pass:
                            is_rec = (bm.tile == m.tile and bm.direction == m.direction)

                    btn_text = f"{'⭐' if is_rec else ''} [{m.tile.a}|{m.tile.b}] {d}"
                    if st.button(
                        btn_text,
                        key=f"m_{i}_{m.direction.value}",
                        use_container_width=True,
                        type="primary" if is_rec else "secondary",
                    ):
                        if gs.turn != Pos.ME:
                            S('msg', "⚠️ ليس دورك الآن!")
                            S('msg_type', 'warning')
                            st.rerun()
                        else:
                            ok = gs.apply(m)
                            if ok:
                                S('log', S('log') + [format_move(m)])

                                if adv and isinstance(adv, dict) and adv.get('all_moves'):
                                    move_label = f"[{m.tile.a}|{m.tile.b}]"
                                    chosen_wr = 0.5
                                    if is_rec:
                                        chosen_wr = safe_float(adv.get('win_rate', 0.5))
                                    else:
                                        for amd in adv['all_moves']:
                                            if amd is None or not isinstance(amd, dict):
                                                continue
                                            # 🛠️ الإصلاح الرابع: قراءة الاسم والنسبة بشكل صحيح للندم
                                            amd_label = safe_str(amd.get('move', ''))
                                            if move_label in amd_label:
                                                chosen_wr = safe_float(amd.get('win_pct', 0.5))
                                                break
                                    regret_entry = RegretTracker.record(
                                        move_label, chosen_wr, adv['all_moves']
                                    )
                                    rh = S('regret_history')
                                    rh.append(regret_entry)
                                    S('regret_history', rh)

                                S('advice', None)
                                S('msg', f"✅ لعبت {m.tile}")
                                S('msg_type', 'success')
                                if gs.game_over:
                                    S('phase', 'over')
                                S('state', gs)
                                st.rerun()
                            else:
                                S('msg', "❌ فشل تطبيق الحركة!")
                                S('msg_type', 'error')
                                st.rerun()

        if any(m.is_pass for m in valid):
            if st.button("🚫 دق (تخطي الدور)", use_container_width=True):
                if gs.turn == Pos.ME:
                    gs.apply(Move(Pos.ME, None, None))
                    S('log', S('log') + ["🟢 أنت: دق 🚫"])

                    adv = S('advice')
                    if adv and isinstance(adv, dict) and adv.get('all_moves'):
                        regret_entry = RegretTracker.record("دق", 0.4, adv['all_moves'])
                        rh = S('regret_history')
                        rh.append(regret_entry)
                        S('regret_history', rh)

                    S('advice', None)
                    S('msg', "🚫 دقيت")
                    S('msg_type', 'warning')
                    if gs.game_over:
                        S('phase', 'over')
                    S('state', gs)
                    st.rerun()

    # ═══════════════════════════════════
    # ★ دور الخصم / الشريك
    # ═══════════════════════════════════
    else:
        name = turn.label
        opp_count = gs.players[turn].count
        st.markdown(f"### {turn.icon} دور: **{name}** ({opp_count} أحجار)")

        pa = PatternAnalyzer(gs)
        cp = pa.analyze_player(turn)
        if cp['confidence'] > 20:
            traits_txt = ''
            for t in cp['traits'][:2]:
                traits_txt += f' | {t}'
            st.markdown(f'''
            <div class="pattern-card" style="padding:10px 16px;">
                <span style="font-size:20px;">{cp['icon']}</span>
                <span style="font-weight:bold;">{name}</span> →
                <span style="color:#CE93D8;font-weight:bold;">{cp['style']}</span>
                {traits_txt}
            </div>
            ''', unsafe_allow_html=True)

        pending = S('pending_tile')
        if pending is not None:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#E65100,#FF9800);border-radius:14px;
            padding:20px;text-align:center;color:#fff;margin:10px 0">
                <div style="font-size:14px">🤔 الحجر يركب في الجهتين!</div>
                <div style="font-size:28px;font-weight:bold;margin:8px 0">[{pending.a}|{pending.b}]</div>
                <div style="font-size:13px">أين وضعه {name}؟</div>
            </div>
            """, unsafe_allow_html=True)
            col_left, _, col_right = st.columns([2, 1, 2])
            btn_key = f"{pending.a}_{pending.b}_{turn.value}"
            with col_left:
                if st.button("⬅️ في اليسار", key=f"pl_{btn_key}", use_container_width=True, type="primary"):
                    if apply_opponent_move(gs, turn, pending, Direction.LEFT):
                        st.rerun()
            with col_right:
                if st.button("في اليمين ➡️", key=f"pr_{btn_key}", use_container_width=True, type="primary"):
                    if apply_opponent_move(gs, turn, pending, Direction.RIGHT):
                        st.rerun()
            st.markdown("")
            if st.button("❌ إلغاء واختيار حجر آخر", key=f"pc_{btn_key}", use_container_width=True):
                S('pending_tile', None)
                st.rerun()

        else:
            remaining = get_remaining_tiles(gs)
            if gs.board.is_empty:
                playable = remaining
            else:
                playable = [t for t in remaining if gs.board.can_play(t)]

            if playable:
                playable.sort(key=lambda t: (t.a, t.b), reverse=True)

                xray = XRayEngine(gs)
                rep = xray.xray_report()[turn]
                certain_tiles = rep['certain']

                st.caption(
                    f"👇 اضغط على الحجر الذي لعبه **{name}** "
                    f"({len(playable)} حجر متاح):"
                )
                ncols = min(len(playable), 5)
                for row_start in range(0, len(playable), ncols):
                    row_tiles = playable[row_start:row_start + ncols]
                    cols = st.columns(ncols)
                    for j, t in enumerate(row_tiles):
                        with cols[j]:
                            is_expected = t in certain_tiles
                            btn_label = (
                                f"🔥 [{t.a}|{t.b}]" if is_expected
                                else f"[{t.a}|{t.b}]"
                            )
                            if st.button(
                                btn_label,
                                key=f"o_{t.a}_{t.b}_{turn.value}",
                                use_container_width=True,
                            ):
                                if gs.board.is_empty:
                                    if apply_opponent_move(gs, turn, t, Direction.LEFT):
                                        st.rerun()
                                else:
                                    dirs = gs.board.can_play(t)
                                    if len(dirs) == 1:
                                        if apply_opponent_move(gs, turn, t, dirs[0]):
                                            st.rerun()
                                    elif len(dirs) >= 2:
                                        S('pending_tile', t)
                                        st.rerun()
                                    else:
                                        S('msg', "❌ الحجر لا يركب هنا!")
                                        S('msg_type', 'error')
                                        st.rerun()
            else:
                st.info("💡 لا توجد أحجار تركب. يجب عليه التخطي.")

            st.markdown("---")
            if st.button(
                f"🚫 {name} دق (باس)",
                key=f"ps_{turn.value}",
                type="primary",
                use_container_width=True,
            ):
                if gs.turn == turn:
                    gs.apply(Move(turn, None, None))
                    S('log', S('log') + [f"{turn.icon} {turn.label}: دق 🚫"])
                    S('advice', None)
                    S('msg', f"🚫 {name} دق")
                    S('msg_type', 'warning')
                    if gs.game_over:
                        S('phase', 'over')
                    S('state', gs)
                    st.rerun()

    st.markdown("---")
    st.markdown("### 🃏 أحجارك المتبقية")
    playable_idx = []
    if not gs.board.is_empty:
        playable_idx = [i for i, t in enumerate(gs.my_hand) if gs.board.can_play(t)]
    else:
        playable_idx = list(range(len(gs.my_hand)))
    if turn != Pos.ME:
        playable_idx = []
    SVG.hand(gs.my_hand, glowing=playable_idx, title="يدك")

    # ─── سجل الندم المباشر ───
    rh = S('regret_history')
    if rh:
        with st.expander(f"😢 سجل الندم ({len(rh)} حركة مُحلّلة)"):
            for i, entry in enumerate(reversed(rh[-10:]), 1):
                regret_val = safe_float(entry.get('regret', 0))
                if regret_val < 0.03:
                    r_icon = "✅"
                    r_text = "قرار مثالي"
                elif regret_val < 0.10:
                    r_icon = "👍"
                    r_text = "قرار جيد"
                elif regret_val < 0.20:
                    r_icon = "😐"
                    r_text = "قرار مقبول"
                else:
                    r_icon = "😬"
                    r_text = f"ندم: -{regret_val:.0%}"

                entry_wr = safe_float(entry.get('win_rate', 0.5))
                entry_move = safe_str(entry.get('move', '?'))
                st.markdown(
                    f"`{len(rh) - i + 1}.` {r_icon} **{entry_move}** "
                    f"(فوز: {entry_wr:.0%}) → {r_text}"
                )
                best_avail = entry.get('best_available')
                if best_avail and regret_val > 0.05:
                    best_wr = safe_float(entry.get('best_win_rate', 0))
                    st.caption(
                        f"   💡 الأفضل كان: {best_avail} "
                        f"({best_wr:.0%})"
                    )

    with st.expander("📜 سجل المعركة"):
        log = S('log')
        if log:
            for i, e in enumerate(reversed(log[-20:]), 1):
                st.markdown(f"`{len(log) - i + 1}.` {e}")
        else:
            st.caption("لم تُسجّل حركات بعد.")


# ═══════════════════════════════════════════════════════
# 🏆 النهاية
# ═══════════════════════════════════════════════════════
elif phase == 'over':
    gs = S('state')
    is_locked = gs.passes >= 4

    win = False
    if not is_locked:
        win = gs.winner and gs.winner.is_friend
        if win:
            st.balloons()
            st.markdown(
                '<div style="text-align:center;padding:40px;'
                'background:linear-gradient(135deg,#1B5E20,#4CAF50);'
                'border-radius:18px;color:#fff;margin:20px 0">'
                '<h1>🏆 مبروك! الانتصار الساحق!</h1></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="text-align:center;padding:40px;'
                'background:linear-gradient(135deg,#B71C1C,#E53935);'
                'border-radius:18px;color:#fff;margin:20px 0">'
                '<h1>😔 خسارة مشرفة</h1></div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<div style="text-align:center;padding:40px;'
            'background:linear-gradient(135deg,#E65100,#FF9800);'
            'border-radius:18px;color:#fff;margin:20px 0">'
            '<h1>🔒 اللعبة مقفولة! لنحسب النقاط..</h1></div>',
            unsafe_allow_html=True,
        )

    st.markdown("### 🎯 الطاولة النهائية")
    SVG.board(gs.board, h=200)

    # ─── تقرير الندم النهائي ───
    rh = S('regret_history')
    if rh:
        summary = RegretTracker.summary(rh)
        if summary:
            st.markdown("---")
            st.markdown("### 😢 تقرير الندم النهائي - تحليل قراراتك")

            gc = summary['grade_color']
            st.markdown(f'''
            <div class="regret-card" style="text-align:center;">
                <div style="font-size:14px;opacity:0.8;">تقييم أدائك الإجمالي</div>
                <div style="font-size:60px;font-weight:bold;color:{gc};margin:10px 0;">
                    {summary['grade']}
                </div>
                <div style="font-size:20px;font-weight:bold;">{summary['grade_label']}</div>
                <div style="display:flex;justify-content:center;gap:30px;margin-top:15px;">
                    <div>
                        <div style="font-size:11px;opacity:0.7;">حركات مثالية</div>
                        <div style="font-size:22px;font-weight:bold;">
                            {summary['perfect_moves']}/{summary['total_moves']}
                        </div>
                    </div>
                    <div>
                        <div style="font-size:11px;opacity:0.7;">متوسط الفوز</div>
                        <div style="font-size:22px;font-weight:bold;">
                            {summary['avg_win_rate']:.0%}
                        </div>
                    </div>
                    <div>
                        <div style="font-size:11px;opacity:0.7;">مجموع الندم</div>
                        <div style="font-size:22px;font-weight:bold;">
                            {summary['total_regret']:.2f}
                        </div>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

            rc1, rc2 = st.columns(2)
            with rc1:
                worst = summary.get('worst_decision')
                if worst and safe_float(worst.get('regret', 0)) > 0.05:
                    st.error(
                        f"😬 **أسوأ قرار:** {safe_str(worst.get('move', '?'))} "
                        f"(فوز {safe_float(worst.get('win_rate', 0)):.0%} "
                        f"بدل {safe_float(worst.get('best_win_rate', 0)):.0%})\n\n"
                        f"الأفضل كان: {safe_str(worst.get('best_available', '?'))}"
                    )
                else:
                    st.success("✅ لم ترتكب أخطاء كبيرة! أداء ممتاز!")
            with rc2:
                best = summary.get('best_decision')
                if best:
                    st.success(
                        f"⭐ **أفضل قرار:** {safe_str(best.get('move', '?'))} "
                        f"(فوز {safe_float(best.get('win_rate', 0)):.0%})"
                    )

            with st.expander("📋 تفاصيل كل حركة"):
                for i, entry in enumerate(rh, 1):
                    regret_val = safe_float(entry.get('regret', 0))
                    if regret_val < 0.03:
                        r_icon = "✅"
                    elif regret_val < 0.10:
                        r_icon = "👍"
                    elif regret_val < 0.20:
                        r_icon = "😐"
                    else:
                        r_icon = "😬"
                    st.markdown(
                        f"`{i}.` {r_icon} **{safe_str(entry.get('move', '?'))}** → "
                        f"فوز {safe_float(entry.get('win_rate', 0)):.0%} "
                        f"(ندم: {regret_val:.0%})"
                    )

    st.markdown("---")
    st.markdown("### 📊 حاسبة النقاط الدقيقة")

    my_pts = sum(t.total for t in gs.my_hand)
    pts_on_board = sum(t.total for t in gs.board.tiles_on_table)
    unplayed_total = 168 - pts_on_board
    others_total = max(0, unplayed_total - my_pts)

    st.info(f"💡 النقاط المتبقية عند الآخرين: **{others_total} نقطة**")

    mc1, mc2 = st.columns(2)
    with mc1:
        st.metric("🟢 نقاط يدك", f"{my_pts}")
    with mc2:
        st.metric("❓ مجموع الآخرين", f"{others_total}")

    st.markdown("#### 🔢 أدخل أوراق الخصم:")
    cc1, cc2 = st.columns(2)
    with cc1:
        opp_pts = st.number_input(
            "🔴 أوراق الخصوم (يمين + يسار):",
            min_value=0,
            max_value=max(1, others_total),
            value=min(max(0, others_total), 10),
        )
    with cc2:
        default_part = max(0, others_total - opp_pts)
        part_pts = st.number_input(
            "🔵 أوراق شريكك:",
            min_value=0,
            max_value=max(1, others_total),
            value=default_part,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if not is_locked:
        if win:
            st.markdown(
                f'<div class="glow-card" style="background:linear-gradient(135deg,#1B5E20,#2E7D32);">'
                f'🎉 فريقك يسجل: <b>{opp_pts}</b> نقطة!</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="glow-card" style="background:linear-gradient(135deg,#B71C1C,#E53935);">'
                f'🔴 الخصوم يسجلون: <b>{my_pts + part_pts}</b> نقطة!</div>',
                unsafe_allow_html=True,
            )
    else:
        our_team = my_pts + part_pts
        their_team = opp_pts
        if our_team < their_team:
            st.markdown(
                f'<div class="glow-card" style="background:linear-gradient(135deg,#1B5E20,#2E7D32);">'
                f'🏆 فريقك فاز بالقفل! ({our_team} &lt; {their_team})<br>'
                f'سجلتم: <b>{their_team}</b> نقطة!</div>',
                unsafe_allow_html=True,
            )
        elif their_team < our_team:
            st.markdown(
                f'<div class="glow-card" style="background:linear-gradient(135deg,#B71C1C,#E53935);">'
                f'🔴 الخصوم فازوا بالقفل! ({their_team} &lt; {our_team})<br>'
                f'سجلوا: <b>{our_team}</b> نقطة!</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="glow-card" style="background:linear-gradient(135deg,#E65100,#FF9800);">'
                f'🤝 تعادل! ({our_team} لكل فريق) - لا أحد يسجل.</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("🔄 العب مباراة جديدة", use_container_width=True, type="primary"):
            reset()
            st.rerun()
    with bc2:
        if st.button("🎓 تدرّب على الأخطاء", use_container_width=True):
            S('phase', 'training')
            S('training_lesson', 0)
            S('training_score', 0)
            S('training_answers', {})
            st.rerun()
