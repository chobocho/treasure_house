// 슬라이드 p3-v2-accessor-override — 재정의는 한정자까지 맞춘다, C# 2.0
using System;

class Shape
{
    public virtual string Name
    {
        get { return "shape"; }
        protected set { }
    }
}

class Circle : Shape
{
    public override string Name
    {
        get { return "circle"; }
        set { }                          // protected is missing
    }
}

class App
{
    static void Main() { }
}
