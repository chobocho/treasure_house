// 슬라이드 p15-v14-xm-container — 확장 블록을 둘 수 있는 곳, C# 14
using System;

static class Ok
{
    extension(int n) { public int Sq => n * n; }
}
#if NONSTATIC
class Plain
{
    extension(int n) { public int Cube => n * n * n; }
}
#elif GENERIC
static class Gen<T>
{
    extension(int n) { public int Cube => n * n * n; }
}
#elif NESTED
static class Outer
{
    public static class Inner
    {
        extension(int n) { public int Cube => n * n * n; }
    }
}
#elif VIRTUAL
static class Mods
{
    extension(int n) { public virtual int Cube => n * n * n; }
}
#endif

class Program
{
    static void Main() => Console.WriteLine(7.Sq);
}
