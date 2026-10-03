// 슬라이드 p11-v10-gu-hide — 같은 이름의 형식이 이긴다, C# 10.0
class Console                                   // global namespace
{
    public static void WriteLine(string s) =>
        System.Console.WriteLine("[mine] " + s);
}

class App
{
    static void Main()
    {
        Console.WriteLine("hello");                 // which Console?
        Math.Abs(-1);                               // System.Math
        System.Console.WriteLine("hello");
    }
}
