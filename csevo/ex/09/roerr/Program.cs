// 슬라이드 p9-v8-ro-err — readonly 멤버가 거절되는 곳, C# 8.0
using System;

struct P
{
    public int X;
    public readonly void Move(int dx) { X += dx; }   // writes this
#if DECL
    public readonly static int Zero() => 0;          // static
#endif
}
#if DECL
class C
{
    public readonly int Get() => 1;                  // a class member
}
#endif

class App
{
    static void Main() => Console.WriteLine(new P().X);
}
