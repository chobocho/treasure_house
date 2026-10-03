// 슬라이드 p11-v10-gu-ext — Where 는 확장으로만 보인다, C# 10.0
class App
{
    static void Main()
    {
        var xs = Range(1, 6);                       // static member
        var even = xs.Where(x => x % 2 == 0);       // extension: ok
        Console.WriteLine(string.Join(",", even));
#if BAD
        var odd = Where(xs, x => x % 2 == 1);       // not as a static
#endif
    }
}
