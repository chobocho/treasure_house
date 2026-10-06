// 슬라이드 p14-v13-pp-rules — 정의 하나, 구현 하나, C# 13.0
using System;

partial class P
{
    public partial int A { get; set; }       // defining
#if !MISSING
    public partial int A { get => 1; set { } }
#endif
#if BOTHAUTO
    public partial int B { get; set; }
    public partial int B { get; set; }        // auto again
#elif TWOIMPL
    public partial int B { get; }
    public partial int B => 2;
    public partial int B => 3;                 // second body
#elif ONLYIMPL
    public partial int B => 2;                 // no defining part
#elif HALF
    public partial int B { get; set; }
    public partial int B { get => 2; set; }   // one body only
#endif
}

class App
{
    static void Main() => Console.WriteLine(new P().A);
}
