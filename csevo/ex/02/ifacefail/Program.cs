// 슬라이드 p2-v1-ifacefail — 인터페이스 구현의 규칙, C# 1.0
interface IStore
{
    void Save();
    int Count { get; }
    void Reset() { }                    // a body: C# 8 feature
}

class Store : IStore
{
    void Save() { }                     // must be public
}

class App
{
    static void Main() { }
}
