// 슬라이드 p2-v1-finalizer — Finalize 를 직접 쓰면, C# 1.0
class Res
{
    protected override void Finalize() { }     // write ~Res() instead
}

struct Buffer
{
    ~Buffer() { }                              // only classes
}

class App
{
    static void Main() { }
}
