// 슬라이드 p14-v13-ri-pref — 패턴의 Dispose 가 먼저다, C# 13.0
using System;

ref struct Two : IDisposable
{
    public void Dispose() => Console.WriteLine("pattern Dispose");
    void IDisposable.Dispose()
        => Console.WriteLine("IDisposable.Dispose");
}

class App
{
    static void Use<T>(T t) where T : IDisposable, allows ref struct
    {
        using (t) { }
    }

    static void Main()
    {
        using (new Two()) { }      // the pattern wins
        Use(new Two());            // only the interface is known
    }
}
