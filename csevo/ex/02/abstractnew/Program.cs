// 슬라이드 p2-v1-abstractfail — 추상 클래스는 new 할 수 없다, C# 1.0
abstract class Animal
{
    public abstract string Sound();
}

class App
{
    static void Main()
    {
        Animal a = new Animal();
    }
}
