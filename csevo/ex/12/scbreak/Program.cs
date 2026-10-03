// 슬라이드 p12-v11-sc-break — 깨지는 변경 둘, C# 11
using System;

ref struct R<T>
{
#if BAD3
    ref T _f;
    public void Store(ref T t) { _f = ref t; }   // try to capture
#endif
    public void MayCaptureArg(ref T t) { }
    public void CannotCaptureArg(scoped ref T t) { }
}

class Program
{
    static R<int> Use(R<int> r)
    {
        int i = 42;
#if DOC
        r.MayCaptureArg(ref i);        // the document's CS8350 case
#endif
        r.CannotCaptureArg(ref i);     // ok
        return r;
    }

    static R<int> MayCapture(in int i = 0) => new R<int>();

    static R<int> CreateDefault()
    {
#if BAD2
        return MayCapture();           // the hidden default argument
#else
        return default;
#endif
    }

    static void Main()
    {
        Use(new R<int>());
        CreateDefault();
        Console.WriteLine("ok");
    }
}
