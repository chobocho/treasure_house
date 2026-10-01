// 슬라이드 p2-v1-sealed — sealed 클래스와 sealed override, C# 1.0
using System;

sealed class Leaf { }
class Twig : Leaf { }                        // cannot derive

class A { public virtual void F() { } }
class B : A { public sealed override void F() { } }
class C : B { public override void F() { } }  // sealed above

class Odd { public sealed void G() { } }     // nothing to seal

class MyString : String { }                   // string is sealed

class App
{
    static void Main() { }
}
