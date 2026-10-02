// 슬라이드 p8-v7_2-refstruct-later — ref struct 의 뒤 버전, C# 13
using System;

ref struct Reader : IDisposable    // C# 13: interfaces allowed
{
    public ReadOnlySpan<char> Rest;
    public Reader(string s) { Rest = s.AsSpan(); }
    public void Dispose() { Console.WriteLine("disposed"); }
}

class App
{
    // C# 13: a type parameter may stand for a ref struct
    static int Len<T>(T x) where T : IDisposable, allows ref struct
    {
        x.Dispose();
        return 1;
    }

    static void Main()
    {
        using (var r = new Reader("abc"))
        {
            Console.WriteLine(r.Rest.Length);
        }
        Console.WriteLine(Len(new Reader("x")));
    }
}
