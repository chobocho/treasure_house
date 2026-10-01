// 슬라이드 p3-v2-constraints — 제약이 없으면, C# 2.0
class App
{
    static T Max<T>(T a, T b)
    {
        return a > b ? a : b;
    }

    static void Main()
    {
        System.Console.WriteLine(Max(3, 7));
    }
}
