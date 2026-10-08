// 슬라이드 p2-v1-static — 정적과 인스턴스를 섞으면, C# 1.0
class Counter
{
    int count;
    public static int Total = 1;
    public int Count { get { return count; } }

    public static void Reset()
    {
        count = 0;                     // no 'this' in a static method
    }

    public void Use(Counter other)
    {
        int t = other.Total;           // static via an instance
    }
}

class App
{
    static void Main() { }
}
