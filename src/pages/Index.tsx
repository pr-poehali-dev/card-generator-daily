import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';
import { toast } from 'sonner';

interface DailyCard {
  id: number;
  date: string;
  title: string;
  message: string;
  image_url: string;
  is_holiday: boolean;
  holiday_name: string | null;
}

const Index = () => {
  const [todayCard, setTodayCard] = useState<DailyCard | null>(null);
  const [chatId, setChatId] = useState('');
  const [isSubscribing, setIsSubscribing] = useState(false);
  const [isSendingTest, setIsSendingTest] = useState(false);

  useEffect(() => {
    loadTodayCard();
  }, []);

  const loadTodayCard = async () => {
    try {
      const response = await fetch('https://functions.poehali.dev/1bd9e508-4b11-466f-822c-712a48a72d8a?action=today');
      if (response.ok) {
        const card = await response.json();
        setTodayCard(card);
      } else {
        toast.error('Не удалось загрузить открытку дня');
      }
    } catch (error) {
      console.error('Error loading card:', error);
      toast.error('Ошибка загрузки открытки');
    }
  };

  const handleSubscribe = async () => {
    if (!chatId.trim()) {
      toast.error('Введите ваш Telegram ID');
      return;
    }

    setIsSubscribing(true);
    try {
      const response = await fetch('https://functions.poehali.dev/2e278bd2-089c-4a78-80f9-462b215b43be', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'subscribe',
          chat_id: parseInt(chatId),
        }),
      });

      if (response.ok) {
        toast.success('Подписка оформлена! Открытки будут приходить каждый день');
        setChatId('');
      } else {
        toast.error('Ошибка подписки. Проверьте правильность ID');
      }
    } catch (error) {
      console.error('Subscribe error:', error);
      toast.error('Ошибка подписки. Попробуйте позже');
    } finally {
      setIsSubscribing(false);
    }
  };

  const handleSendTestCards = async () => {
    setIsSendingTest(true);
    try {
      const response = await fetch('https://functions.poehali.dev/984850e6-4ae1-4f9d-bf71-cba8c51bdafe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          days: 3,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        toast.success(`Отправлено ${result.sent_count} открыток за 3 дня!`);
      } else {
        toast.error('Ошибка отправки открыток');
      }
    } catch (error) {
      console.error('Send test error:', error);
      toast.error('Ошибка отправки');
    } finally {
      setIsSendingTest(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#FEF7CD] via-[#FEC6A1] to-[#F97316]">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-10 left-10 text-white/10 text-9xl">🍂</div>
        <div className="absolute top-40 right-20 text-white/10 text-7xl">🍁</div>
        <div className="absolute bottom-20 left-20 text-white/10 text-8xl">🌿</div>
        <div className="absolute bottom-40 right-40 text-white/10 text-6xl">🍂</div>
      </div>

      <div className="container mx-auto px-4 py-12 relative z-10">
        <header className="text-center mb-12 animate-fade-in">
          <h1 className="text-6xl font-bold text-white mb-4 drop-shadow-lg">
            Открытки на каждый день
          </h1>
          <p className="text-xl text-white/90 drop-shadow">
            Душевные пожелания в русском стиле
          </p>
        </header>

        {todayCard && (
          <div className="max-w-3xl mx-auto mb-16 animate-scale-in">
            <div className="flex items-center justify-center gap-3 mb-6">
              <Badge className="bg-white/90 text-primary text-lg px-6 py-2 hover:bg-white">
                <Icon name="Calendar" className="mr-2" size={20} />
                Открытка дня
              </Badge>
              {todayCard.is_holiday && todayCard.holiday_name && (
                <Badge className="bg-secondary/90 text-white text-lg px-6 py-2">
                  <Icon name="Star" className="mr-2" size={20} />
                  {todayCard.holiday_name}
                </Badge>
              )}
            </div>

            <Card className="overflow-hidden shadow-2xl border-4 border-white/50 backdrop-blur-sm bg-white/95 hover-scale transition-all duration-300">
              <div className="relative">
                <img
                  src={todayCard.image_url}
                  alt={todayCard.title}
                  className="w-full h-auto object-cover"
                />
              </div>
            </Card>
          </div>
        )}

        <div className="max-w-2xl mx-auto">
          <Card className="p-8 bg-white/95 backdrop-blur-sm shadow-xl border-2 border-white/50 animate-fade-in">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-full bg-primary/10">
                <Icon name="Send" className="text-primary" size={32} />
              </div>
              <div>
                <h2 className="text-3xl font-bold text-foreground">
                  Подписка на Telegram
                </h2>
                <p className="text-muted-foreground text-lg">
                  Получайте открытки каждый день прямо в мессенджер
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="bg-accent/30 p-4 rounded-lg border border-accent">
                <p className="text-sm text-foreground mb-2 flex items-start gap-2">
                  <Icon name="Info" size={18} className="mt-0.5 flex-shrink-0" />
                  <span>
                    Чтобы узнать свой Telegram ID:
                    <br />
                    1. Напишите боту{' '}
                    <a
                      href="https://t.me/userinfobot"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary underline hover:text-primary/80"
                    >
                      @userinfobot
                    </a>
                    <br />
                    2. Скопируйте ваш ID и вставьте в поле ниже
                  </span>
                </p>
              </div>

              <div className="flex gap-3">
                <Input
                  type="text"
                  placeholder="Ваш Telegram ID"
                  value={chatId}
                  onChange={(e) => setChatId(e.target.value)}
                  className="flex-1 h-12 text-lg"
                />
                <Button
                  onClick={handleSubscribe}
                  disabled={isSubscribing}
                  className="h-12 px-8 text-lg font-semibold bg-primary hover:bg-primary/90"
                  size="lg"
                >
                  {isSubscribing ? (
                    <>
                      <Icon name="Loader2" className="mr-2 animate-spin" size={20} />
                      Подписка...
                    </>
                  ) : (
                    <>
                      <Icon name="Check" className="mr-2" size={20} />
                      Подписаться
                    </>
                  )}
                </Button>
              </div>
            </div>
          </Card>
        </div>

        <div className="max-w-2xl mx-auto mt-8">
          <Card className="p-6 bg-white/90 backdrop-blur-sm shadow-lg border-2 border-white/50">
            <div className="text-center">
              <h3 className="text-xl font-bold text-foreground mb-3">
                Тестовая отправка
              </h3>
              <p className="text-muted-foreground mb-4">
                Отправить открытки за последние 3 дня всем подписчикам
              </p>
              <Button
                onClick={handleSendTestCards}
                disabled={isSendingTest}
                className="bg-secondary hover:bg-secondary/90"
                size="lg"
              >
                {isSendingTest ? (
                  <>
                    <Icon name="Loader2" className="mr-2 animate-spin" size={20} />
                    Отправка...
                  </>
                ) : (
                  <>
                    <Icon name="Send" className="mr-2" size={20} />
                    Отправить тестовые открытки
                  </>
                )}
              </Button>
            </div>
          </Card>
        </div>

        <div className="text-center mt-12 text-white/80">
          <p className="text-lg flex items-center justify-center gap-2">
            <Icon name="Heart" size={20} className="text-red-400" />
            Создано с любовью
          </p>
        </div>
      </div>
    </div>
  );
};

export default Index;