// 슬라이드 p3-v2-partial-conflict — 서로 어긋나는 조각들, C# 2.0
using System;

partial class A : EventArgs { }        // another base class
internal partial class B { }           // another accessibility
partial class C { public void Run() { } }   // the same member
partial class D { }                    // the other part lacks partial

class App
{
    static void Main() { }
}
