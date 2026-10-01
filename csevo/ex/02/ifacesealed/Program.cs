// 슬라이드 p2-v1-ifacecast — sealed 클래스면 컴파일 때 막힌다, C# 1.0
interface IFly { void Fly(); }

sealed class Stone { }

class App
{
    static void Main()
    {
        Stone s = new Stone();
        IFly f = (IFly)s;              // no subclass can ever add IFly
    }
}
