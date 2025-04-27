#include <vector>

#include "layer.hpp"

using namespace std;

Graph::Graph(int size) {
    _mem = new Vertex[size];
    _size = size;

    for(size_t id = 0; id < _size; ++id) {
        _mem[id].id = id;
        _mem[id].score = -1;
        _mem[id].weight = -1;
        _mem[id].codegree = 0;
    }
}

Graph::~Graph() {
    delete [] _mem;
}

void Graph::add_edge(int start, int end) {
    if(start < 0 || size_t(start) >= _size || end < 0 || size_t(end) >= _size) {
        throw Error("В add_edge недопустимые аргументы");
    }

    _mem[start].children.push_back(&_mem[end]);
    _mem[end].parents.push_back(&_mem[start]);

    _mem[end].codegree += 1;
}

void Graph::set_weights(const std::vector<int>& weights) {
    if(weights.size() != _size) {
        throw Error("В set_weights передан массив неподходящего размера");
    }

    for(size_t id = 0; id < _size; ++id) {
        _mem[id].weight = weights[id];
    }
}

void Graph::set_score(int id, int score) {
    if(id < 0 || size_t(id) >= _size) {
        throw Error("Неправильный id в set_score");
    }

    _mem[id].score = score;
}

vector<int> Graph::in_vertices() const{
    vector<int> ret;

    for(size_t id = 0; id < _size; ++id) {
        if(_mem[id].parents.size() == 0) {
            ret.push_back(id);
        }
    }

    return ret;
}

Layer::Layer(int max_score) {
    _graph = nullptr;
    _cache = nullptr;

    _max_score = max_score;
}

void Layer::start() {
    if(_graph == nullptr || _cache == nullptr) {
        throw Error("Необходимо сначала проинициализировать граф и кэш");
    }

    if(_graph -> size() == 0) {
        throw Error("Граф пуст");
    }

    std::vector<int> ids = _graph -> in_vertices();
    if(ids.size() == 0) {
        throw Error("Не найдены входные вершины");
    }

    for(auto& id: ids) {
        if(_graph -> at(id).score < 0 || _graph -> at(id).weight < 0) {
            //cout << endl;
            //cout << "id: " << id << endl;
            //cout << "score: " << _graph -> at(id).score << endl;
            //cout << "weight: " << _graph -> at(id).weight << endl;
            //cout << endl;
            throw Error("Скор или вес входной вершины меньше нуля в Layer::start()");
        }
    }

    _mem = std::set<LayerNode*>();
    _lists = std::vector<LayerNode*>(_max_score + 1, nullptr);
    _curr_min = _max_score;
    for(size_t i = 0; i < ids.size(); ++i) {
        int id = ids[i];
        int score = _graph -> at(id).score;

        if(_curr_min > score) {
            _curr_min = score;
        }

        if(score > _max_score) {
            throw Error("score > _max_score");
        }

        auto ptr = new LayerNode;
        _mem.insert(ptr);
        ptr -> vertex = &(_graph -> at(id));

        if(_lists[score] == nullptr) {
            _lists[score] = ptr;

            ptr -> prev = nullptr;
            ptr -> next = nullptr;
        }
        else {
            _lists[score] -> prev = ptr;

            ptr -> prev = nullptr;
            ptr -> next = _lists[score];

            _lists[score] = ptr;
        }

        _id2node.insert({id, ptr});
    }
}

int Layer::step() {
    //cout << endl;

    vector<int> recalculate_ids; // Номера вершин, для которых надо пересчитать скор

    // Пушим в кэш то, что используется и сохраняем id того, что вытолкнется

    int id = _lists[_curr_min] -> vertex -> id;
    //cout << "Выбрана вершина " << id << endl;
    int weight = _lists[_curr_min] -> vertex -> weight;

    auto cache_garbage = _cache -> push(id, weight);
    for(auto& entry: cache_garbage) {
        recalculate_ids.push_back(entry.id);
    }

    for(auto& parent: _id2node[id] -> vertex -> parents) {
        auto cache_garbage = _cache -> push(parent -> id, parent -> weight);
        for(auto& entry: cache_garbage) {
            recalculate_ids.push_back(entry.id);
        }
    }

    //cout << "Родители: " << (_id2node[id] -> vertex -> parents2string()) << endl;
    //cout << "Пересчитываемые вершины: " << container2string(recalculate_ids) << endl;

    // Удаляем выбранную вешнину

    //cout << "Размер слоя: " << _mem.size() << endl;
    //cout << "Текущий минимальный скор: " << _curr_min << endl;

    if(_id2node[id] -> next == nullptr) {
        //cout << "A" << endl;
        _lists[_curr_min] = nullptr;

        while(_lists[_curr_min] == nullptr) {
            ++_curr_min;

            if(_curr_min > _max_score) {
                _curr_min = _max_score;
            
                break;
            }
        }

        _mem.erase(_id2node[id]);
        delete _id2node[id];
        _id2node.erase(id);
    }
    else {
        //cout << "B" << endl;
        _id2node[id] -> next -> prev = nullptr;
        _lists[_curr_min] = _id2node[id] -> next;

        _mem.erase(_id2node[id]);
        delete _id2node[id];
        _id2node.erase(id);
    }

    // Смотрим на детей выброшенной вершины
    // Добавляем их в слой, если нужно

    auto children = _graph -> at(id).children;
    //cout << "Дети: " << (_graph -> at(id)).children2string() << endl;
    //cout << "Подходят: ";
    for(Graph::Vertex* child: children) {
        child -> codegree -= 1;

        if(child -> codegree == 0) {
            //cout << child -> id << " ";

            auto node = new LayerNode;
            node -> vertex = &(_graph -> at(child -> id));
            
            int score = 0;
            if(!_cache -> contains(child -> id)) {
                score += child -> weight;
            }
            for(Graph::Vertex* parent: child->parents) {
                if(!_cache -> contains(parent -> id)) {
                    score += parent -> weight;
                }
            }
            node -> vertex -> score = score;
            
            if(score > _max_score) {
                throw Error("score > _max_score");
            }

            _mem.insert(node);
            _id2node.insert({node -> vertex -> id, node});
            
            if(_lists[score] == nullptr) {
                _lists[score] = node;

                node -> prev = nullptr;
                node -> next = nullptr;
            }
            else {
                _lists[score] -> prev = node;

                node -> prev = nullptr;
                node -> next = _lists[score];

                _lists[score] = node;
            }

            _curr_min = min(_curr_min, score);
        }
    }
    //cout << endl;

    // Пересчитываем скоры, где это требуется

    for(auto& recalc_id: recalculate_ids) {
        if(!_id2node.contains(recalc_id)) {
            continue;
        }

        LayerNode* node = _id2node[recalc_id];
        Graph::Vertex* vertex = node -> vertex;

        int new_score = 0;
        if(!_cache -> contains(vertex -> id)) {
            new_score += vertex -> weight;
        }
        for(Graph::Vertex* parent: vertex->parents) {
            if(!_cache -> contains(parent -> id)) {
                new_score += parent -> weight;
            }
        }
        
        if(new_score == vertex -> score) {
            continue;
        }

        if(node -> prev == nullptr && node -> next == nullptr) {
            _lists[vertex -> score] = nullptr;
        }
        else if(node -> prev == nullptr && node -> next != nullptr) {
            node -> next -> prev = nullptr;
            _lists[vertex -> score] = node -> next;
        }
        else if(node -> prev != nullptr && node -> next) {
            node -> prev -> next = nullptr;
        }
        else {
            node -> prev -> next = node -> next;
            node -> next -> prev = node -> prev;
        }

        if(_lists[new_score] == nullptr) {
            node -> prev = nullptr;
            node -> next = nullptr;
             _lists[new_score] = node;
        }
        else {
            node -> prev = nullptr;
            node -> next = _lists[new_score];
            _lists[new_score] -> prev = node;
            _lists[new_score] = node;
        }

        if(new_score < _curr_min) {
            _curr_min = new_score;
        }
        else if(_lists[_curr_min] == nullptr) {
            while(_lists[_curr_min] == nullptr) {
                ++_curr_min;

                if(_curr_min > _max_score) {
                    _curr_min = _max_score;  
                          
                    break;
                }
            }
        }

        vertex -> score = new_score;
    }

    return id;
}