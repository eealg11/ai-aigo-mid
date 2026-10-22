# STREAMING_CHUNK:Importing required Flask and system modules...
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # GAS 및 외부 교차 출처 요청(CORS) 허용

# STREAMING_CHUNK:Defining FixedSizeQueue class and required 11 operations...
class FixedSizeQueue:
    """
    고정 길이 원형 큐(Fixed-Size Circular Queue) 구현 클래스
    """
    def __init__(self, capacity: int = 5):
        """1) 초기화: 지정된 크기로 큐를 생성하고 포인터 및 상태 변수 초기화"""
        self.capacity = capacity
        self.que = [None] * capacity  # 고정 크기 배열 메모리 할당
        self.front = 0                 # 프론트 포인터 (데크 위치)
        self.rear = 0                  # 리어 포인터 (인큐 위치)
        self.no = 0                    # 현재 저장된 데이터 개수

    def is_empty(self) -> bool:
        """4-1) 상태검사: 큐가 비어있는지 확인"""
        return self.no <= 0

    def is_full(self) -> bool:
        """4-2) 상태검사: 큐가 가득 찼는지 확인"""
        return self.no >= self.capacity

    def push(self, value):
        """2-1) Push (Enqueue): 데이터를 큐의 Rear에 추가"""
        if self.is_full():
            raise IndexError("Queue Overflow: 큐가 가득 찼습니다.")
        self.que[self.rear] = value
        self.rear = (self.rear + 1) % self.capacity
        self.no += 1
        return value

    def pop(self):
        """2-2) Pop (Dequeue): Front 위치의 데이터를 추출 및 제거"""
        if self.is_empty():
            raise IndexError("Queue Underflow: 큐가 비어 있습니다.")
        val = self.que[self.front]
        self.que[self.front] = None
        self.front = (self.front + 1) % self.capacity
        self.no -= 1
        return val

    def size((self) -> int:
        """3) 현재 데이터 개수(길이/크기) 반환"""
        return self.no

    def peek(self):
        """5) 전면(Front) 데이터 확인"""
        if self.is_empty():
            raise IndexError("Queue is Empty: 조회할 데이터가 없습니다.")
        return self.que[self.front]

    def clear(self):
        """6) 큐 전체 데이터 삭제"""
        self.que = [None] * self.capacity
        self.front = 0
        self.rear = 0
        self.no = 0

    def find(self, value) -> int:
        """7) 값의 index 검색 (Front부터 논리적 순서대로 탐색하여 상대 인덱스 반환, 없으면 -1)"""
        for i in range(self.no):
            idx = (self.front + i) % self.capacity
            if self.que[idx] == value:
                return i  # Front 기준 0번째부터 몇 번째 위치에 있는지 반환
        return -1

    def count(self, value) -> int:
        """8) 특정 값의 개수(길이/크기) 반환"""
        cnt = 0
        for i in range(self.no):
            idx = (self.front + i) % self.capacity
            if self.que[idx] == value:
                cnt += 1
        return cnt

    def contains(self, value) -> bool:
        """9) 값의 존재 여부 검사"""
        return self.find(value) != -1

    def dump(self) -> list:
        """10) Front 부터 Rear 까지 저장된 논리적 순서대로의 데이터 출력/리스트 반환"""
        result = []
        for i in range(self.no):
            idx = (self.front + i) % self.capacity
            result.append(self.que[idx])
        return result

    def raw_array(self) -> list:
        """11) 물리적 배열 전체 상태 출력"""
        return self.que


# STREAMING_CHUNK:Initializing global queue server instance and endpoints...
# 싱글톤 형태의 글로벌 큐 인스턴스 (기본 용량: 5)
global_queue = FixedSizeQueue(capacity=5)

@app.route('/health', methods=['GET'])
def health_check():
    """서버 헬스 체크 및 연결 상태 확인 앤드포인트"""
    return jsonify({
        "status": "online",
        "message": "Google Cloud Run Fixed-Size Queue Service is Running!"
    }), 200

@app.route('/api/queue', methods=['POST'])
def handle_queue_operation():
    """
    큐 관련 API 요청을 일괄 처리하는 엔드포인트
    Request JSON 예시:
    {
        "action": "push",  # init, push, pop, size, state, peek, clear, find, count, contains, dump, raw_array
        "value": 10,        # push, find, count, contains 시 전달
        "capacity": 5       # init 시 전달
    }
    """
    global global_queue
    data = request.get_json() or {}
    action = data.get('action', '').lower()
    val = data.get('value', None)
    
    try:
        result_payload = {}
        
        # 1) 초기화
        if action == 'init':
            cap = int(data.get('capacity', 5))
            global_queue = FixedSizeQueue(capacity=cap)
            result_payload = {"message": f"큐가 크기 {cap}(으)로 성공적으로 초기화되었습니다."}
            
        # 2) Push
        elif action == 'push':
            if val is None or val == "":
                return jsonify({"error": "Push할 값이 입력되지 않았습니다."}), 400
            pushed_val = global_queue.push(val)
            result_payload = {"message": f"값 '{pushed_val}'이(가) Push 되었습니다.", "pushed": pushed_val}
            
        # 2) Pop
        elif action == 'pop':
            popped_val = global_queue.pop()
            result_payload = {"message": f"값 '{popped_val}'이(가) Pop 되었습니다.", "popped": popped_val}
            
        # 3) 현재 데이터 개수 반환
        elif action == 'size':
            result_payload = {"size": global_queue.size(), "capacity": global_queue.capacity}
            
        # 4) 상태 검사 (full/empty)
        elif action == 'state':
            result_payload = {
                "is_empty": global_queue.is_empty(),
                "is_full": global_queue.is_full()
            }
            
        # 5) 전면(Front) 데이터 확인
        elif action == 'peek':
            result_payload = {"front_value": global_queue.peek()}
            
        # 6) 큐 전체 데이터 삭제
        elif action == 'clear':
            global_queue.clear()
            result_payload = {"message": "큐 전체 데이터가 성공적으로 삭제되었습니다."}
            
        # 7) 값의 index 검색
        elif action == 'find':
            idx = global_queue.find(val)
            result_payload = {"searched_value": val, "relative_index": idx}
            
        # 8) 값의 개수
        elif action == 'count':
            cnt = global_queue.count(val)
            result_payload = {"searched_value": val, "count": cnt}
            
        # 9) 값의 존재 여부 검사
        elif action == 'contains':
            exists = global_queue.contains(val)
            result_payload = {"searched_value": val, "exists": exists}
            
        # 10) Front 부터 Rear 까지 출력
        elif action == 'dump':
            result_payload = {"dump": global_queue.dump()}
            
        # 11) 배열 전체 출력
        elif action == 'raw_array':
            result_payload = {"raw_array": global_queue.raw_array()}
            
        else:
            return jsonify({"error": f"지원하지 않는 action입니다: {action}"}), 400

        # 공통 현재 상태 포함하여 응답
        response_data = {
            "success": True,
            "action": action,
            "result": result_payload,
            "queue_state": {
                "front": global_queue.front,
                "rear": global_queue.rear,
                "count": global_queue.size(),
                "capacity": global_queue.capacity,
                "is_empty": global_queue.is_empty(),
                "is_full": global_queue.is_full(),
                "dump": global_queue.dump(),
                "raw_array": global_queue.raw_array()
            }
        }
        return jsonify(response_data), 200

    except IndexError as ie:
        return jsonify({"success": False, "error": str(ie)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"서버 내부 오류: {str(e)}"}), 500


if __name__ == '__main__':
    # Cloud Run은 PORT 환경변수를 전달하므로 이에 맞추어 포트 바인딩
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
import os
import traceback
from flask import Flask, request, jsonify
from queue_engine import CircularQueue

app = Flask(__name__)

# 전역 고정 길이 큐 인스턴스 (기본 크기: 5)
global_queue = CircularQueue(capacity=5)

@app.errorhandler(Exception)
def handle_global_exception(e):
    """
    서버 내부에서 예외가 발생하더라도 구글 500 HTML 대신
    클라이언트가 이해할 수 있는 JSON 형태로 에러 응답 반환
    """
    error_trace = traceback.format_exc()
    print(f"[SERVER ERROR TRACE]\n{error_trace}") # Cloud Run 로그 기록용
    
    return jsonify({
        "success": False,
        "error": f"서버 내부 처리 오류: {str(e)}",
        "detail": str(e)
    }), 200 # 클라이언트 파싱 실패 방지를 위해 200 전달 또는 JSON 구조 유지

@app.route('/api/queue', methods=['POST'])
def queue_api():
    """
    고정 길이 큐 요청 처리 API
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        action = data.get('action', 'info')
        
        # 1) 초기화
        if action == 'init':
            capacity = int(data.get('capacity', 5))
            res = global_queue.init(capacity)
            
        # 2) Push
        elif action == 'push':
            value = data.get('value')
            if value is None:
                return jsonify({"success": False, "error": "push 할 value 값이 필요합니다."}), 200
            res = global_queue.push(value)
            
        # 3) Pop
        elif action == 'pop':
            res = global_queue.pop()
            
        # 4) Size / Capacity
        elif action == 'size':
            res = {"size": global_queue.size(), "capacity": global_queue.capacity}
            
        # 5) Full / Empty 상태 검사
        elif action == 'status':
            res = {
                "is_empty": global_queue.is_empty(),
                "is_full": global_queue.is_full()
            }
            
        # 6) Peek
        elif action == 'peek':
            res = {"front_element": global_queue.peek()}
            
        # 7) Clear
        elif action == 'clear':
            res = global_queue.clear()
            
        # 8) Find index
        elif action == 'find':
            value = data.get('value')
            res = {"value": value, "index": global_queue.find(value)}
            
        # 9) Count
        elif action == 'count':
            value = data.get('value')
            res = {"value": value, "count": global_queue.count(value)}
            
        # 10) Contains
        elif action == 'contains':
            value = data.get('value')
            res = {"value": value, "exists": global_queue.contains(value)}
            
        # 11) Dump (Front to Rear)
        elif action == 'dump':
            res = {"dump": global_queue.dump()}
            
        # 12) Raw Array
        elif action == 'raw_array':
            res = {"raw_array": global_queue.get_raw_array()}
            
        # 13) Info (모든 상태 종합 반환)
        elif action == 'info':
            res = global_queue.get_full_info()
            
        else:
            return jsonify({"success": False, "error": f"알 수 없는 action: {action}"}), 200

        # 전체 큐의 현재 상태를 포함하여 응답 반환
        return jsonify({
            "success": True,
            "action": action,
            "result": res,
            "state": global_queue.get_full_info()
        }), 200

    except Exception as ex:
        print(f"[API ERROR] {str(ex)}")
        return jsonify({
            "success": False,
            "error": f"API 수행 중 예외 발생: {str(ex)}"
        }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
