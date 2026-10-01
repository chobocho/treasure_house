// 슬라이드 p2-v1-abstractfail — 추상 멤버의 선언 규칙, C# 1.0
abstract class Animal
{
    public abstract string Sound();
    public abstract string Name() { return "?"; }   // body not allowed
}

class Fish : Animal { }                    // Sound not implemented

class Plant
{
    public abstract void Grow();           // class is not abstract
}

class App
{
    static void Main() { }
}
