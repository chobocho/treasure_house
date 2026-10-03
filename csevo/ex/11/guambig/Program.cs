// 슬라이드 p11-v10-gu-ambig — 이 파일에서만 별칭으로 고른다, C# 10.0
#if !BAD
using Timer = System.Threading.Timer;
#endif

class App
{
    static void Main()
    {
        using var t = new Timer(_ => { }, null, Timeout.Infinite, 0);
        Console.WriteLine(t.GetType().FullName);
    }
}
