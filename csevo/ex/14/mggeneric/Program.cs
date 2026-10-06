// 슬라이드 p14-v13-mg-generic — 형식 인수 없는 제네릭을 뺀다, C# 13
using System;

class C
{
    public void M<T>(T t) => Console.WriteLine("C.M<T>");
}

#if !NOEXT
static class E
{
    public static void M(this C c, int x) => Console.WriteLine("E.M");
}
#endif

class Program
{
    static void Main()
    {
        var f = new C().M;       // generic M<T> without type arguments
        f(1);
        Console.WriteLine(f.GetType().Name);
    }
}
