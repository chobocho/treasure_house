// 슬라이드 p5-v4-var-where — 변성은 인터페이스와 대리자에만, C# 4.0
class Box<out T>
{
}

struct Pair<in T>
{
}

class Program
{
    static void M<out T>() { }

    static void Main()
    {
    }
}
